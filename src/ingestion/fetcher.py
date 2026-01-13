import datetime
import re
import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser
from urllib.parse import quote_plus, urljoin
from src.system.logger import setup_logger
from src.system.config_loader import load_config

logger = setup_logger("fetcher")
config = load_config()


# ============================================================
# Unified date parser
# ============================================================
def parse_date(text: str) -> datetime.date:
    """Parse various news date formats into datetime.date."""
    if not text:
        return datetime.date.today()

    text = text.strip()
    today = datetime.date.today()
    now = datetime.datetime.now()

    try:
        # Relative times
        if text in ["刚刚", "刚刚发布"]:
            return today

        m = re.match(r"(\d+)\s*分钟前", text)
        if m:
            return (now - datetime.timedelta(minutes=int(m.group(1)))).date()

        m = re.match(r"(\d+)\s*小时前", text)
        if m:
            return (now - datetime.timedelta(hours=int(m.group(1)))).date()

        m = re.match(r"(\d+)\s*天前", text)
        if m:
            return (now - datetime.timedelta(days=int(m.group(1)))).date()

        if text == "昨天":
            return today - datetime.timedelta(days=1)

        if text == "前天":
            return today - datetime.timedelta(days=2)

        # Time only (e.g., 财联社格式: 10:33 → today)
        if re.match(r"^\d{1,2}:\d{2}$", text):
            return today

        # Chinese date format: 2025年01月02日
        m = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text)
        if m:
            y, mth, d = map(int, m.groups())
            return datetime.date(y, mth, d)

        # Common formats: 2025-01-02 / 2025/01/02 / 2025-01-02 10:33
        dt = parser.parse(text)
        return dt.date()

    except Exception as e:
        logger.warning(f"Failed to parse date '{text}': {e}")
        return today


# ============================================================
# Filter today's news
# ============================================================
def filter_today(news_list: list[dict]) -> list[dict]:
    today = datetime.date.today()
    return [item for item in news_list if item.get("pub_date") == today]


# ============================================================
# RSS fetcher
# ============================================================
def fetch_rss(url: str) -> list[dict]:
    items = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            try:
                pub = parser.parse(entry.published).date()
            except Exception:
                pub = datetime.date.today()

            items.append({
                "title": entry.title,
                "link": entry.link,
                "summary": entry.get("summary", ""),
                "pub_date": pub
            })
    except Exception as e:
        logger.error(f"Failed to fetch RSS: {url} | {e}")
    return items


# ============================================================
# HTML fetcher
# ============================================================
def fetch_html(url: str, selectors: dict) -> list[dict]:
    items = []
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for div in soup.select(selectors.get("item", "")):
            try:
                title = div.select_one(selectors.get("title")).get_text(strip=True)
                link = div.select_one(selectors.get("link"))["href"]
                time_text = div.select_one(selectors.get("time")).get_text(strip=True)
                pub = parse_date(time_text)

                # Fix relative links
                if link.startswith("/"):
                    link = urljoin(url, link)

                items.append({
                    "title": title,
                    "link": link,
                    "summary": "",
                    "pub_date": pub
                })
            except Exception as e:
                logger.warning(f"Failed to parse one HTML entry from {url}: {e}")

    except Exception as e:
        logger.error(f"Failed to fetch HTML: {url} | {e}")
    return items


# ============================================================
# Google News fetcher
# ============================================================
def fetch_google_news(base_url: str, keywords: list[str]) -> list[dict]:
    items = []
    for kw in keywords:
        encoded_kw = quote_plus(kw)
        url = base_url.format(keyword=encoded_kw)
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                try:
                    pub = parser.parse(entry.published).date()
                except Exception:
                    pub = datetime.date.today()

                items.append({
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.get("summary", ""),
                    "pub_date": pub
                })
        except Exception as e:
            logger.error(f"Failed to fetch Google News for keyword '{kw}': {e}")
    return items


# ============================================================
# Main function: fetch all news
# ============================================================
def fetch_all_news() -> list[dict]:
    logger.info("Starting news fetch...")

    items: list[dict] = []

    for source_name in config.get("fetch_order", []):
        src_cfg = config.get("news_sources", {}).get(source_name)
        if not src_cfg or not src_cfg.get("enabled", False):
            continue

        logger.info(f"Fetching news source: {source_name}")
        try:
            if src_cfg["type"] == "rss":
                items.extend(fetch_rss(src_cfg["url"]))
            elif src_cfg["type"] == "html":
                items.extend(fetch_html(src_cfg["url"], src_cfg["selectors"]))
            elif src_cfg["type"] == "google":
                items.extend(fetch_google_news(src_cfg["base_url"], src_cfg["keywords"]))
            else:
                logger.warning(f"Unknown news source type: {source_name}")
        except Exception as e:
            logger.error(f"Failed to fetch {source_name}: {e}")

    # Deduplicate by title
    unique = {item["title"]: item for item in items}
    all_news = list(unique.values())

    # Keep only today's news
    final = filter_today(all_news)

    logger.info(f"Fetched {len(final)} news items for today.")
    return final