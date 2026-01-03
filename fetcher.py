import datetime
import re
import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser
from utils import setup_logger
from config_loader import load_config
from urllib.parse import quote_plus

logger = setup_logger("fetcher")
config = load_config()


# ============================================================
# 统一日期解析模块
# ============================================================
def parse_date(text):
    """统一解析各种新闻日期格式，返回 datetime.date"""

    if not text:
        return datetime.date.today()

    text = text.strip()
    today = datetime.date.today()
    now = datetime.datetime.now()

    # 相对时间
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

    # 财联社格式：10:33 → 默认今天
    if re.match(r"^\d{1,2}:\d{2}$", text):
        return today

    # 中文日期：2025年01月02日
    m = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text)
    if m:
        y, mth, d = map(int, m.groups())
        return datetime.date(y, mth, d)

    # 常见格式：2025-01-02 / 2025/01/02 / 2025-01-02 10:33
    try:
        dt = parser.parse(text)
        return dt.date()
    except:
        pass

    return today


# ============================================================
# 过滤当天新闻
# ============================================================
def filter_today(news_list):
    today = datetime.date.today()
    return [item for item in news_list if item.get("pub_date") == today]


# ============================================================
# RSS 抓取通用函数
# ============================================================
def fetch_rss(url):
    items = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            try:
                pub = parser.parse(entry.published).date()
            except:
                pub = datetime.date.today()

            items.append({
                "title": entry.title,
                "link": entry.link,
                "summary": entry.get("summary", ""),
                "pub_date": pub
            })
    except Exception as e:
        logger.error(f"RSS 抓取失败：{url} | {e}")

    return items


# ============================================================
# HTML 抓取通用函数
# ============================================================
def fetch_html(url, selectors):
    items = []

    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        for div in soup.select(selectors["item"]):
            try:
                title = div.select_one(selectors["title"]).get_text(strip=True)
                link = div.select_one(selectors["link"])["href"]
                time_text = div.select_one(selectors["time"]).get_text(strip=True)
                pub = parse_date(time_text)

                # 修复相对链接
                if link.startswith("/"):
                    from urllib.parse import urljoin
                    link = urljoin(url, link)

                items.append({
                    "title": title,
                    "link": link,
                    "summary": "",
                    "pub_date": pub
                })
            except Exception as e:
                logger.warning(f"HTML 单条解析失败：{e}")

    except Exception as e:
        logger.error(f"HTML 抓取失败：{url} | {e}")

    return items

# ============================================================
# Google 抓取函数
# ============================================================
def fetch_google_news(base_url, keywords):
    items = []

    for kw in keywords:
        # 关键：对关键词做 URL 编码，空格等会变成 +
        encoded_kw = quote_plus(kw)
        url = base_url.format(keyword=encoded_kw)

        try:
            feed = feedparser.parse(url)

            for entry in feed.entries:
                try:
                    pub = parser.parse(entry.published).date()
                except:
                    pub = datetime.date.today()

                items.append({
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.get("summary", ""),
                    "pub_date": pub
                })

        except Exception as e:
            logger.error(f"Google News 抓取失败：{kw} | {e}")

    return items

# ============================================================
# 主函数：根据 config.yaml 自动抓取所有新闻
# ============================================================
def fetch_all_news():
    logger.info("开始抓取新闻…")

    items = []

    # 按配置文件中的顺序抓取
    for source_name in config.get("fetch_order", []):
        src_cfg = config["news_sources"].get(source_name)

        if not src_cfg or not src_cfg.get("enabled", False):
            continue

        logger.info(f"抓取新闻源：{source_name}")

        try:
            if src_cfg["type"] == "rss":
                items += fetch_rss(src_cfg["url"])

            elif src_cfg["type"] == "html":
                items += fetch_html(src_cfg["url"], src_cfg["selectors"])

            elif src_cfg["type"] == "google":
                items += fetch_google_news(
                    src_cfg["base_url"],
                    src_cfg["keywords"]
                )

            else:
                logger.warning(f"未知新闻源类型：{source_name}")

        except Exception as e:
            logger.error(f"抓取 {source_name} 失败：{e}")

    # 去重（按标题）
    unique = {}
    for item in items:
        if item["title"] not in unique:
            unique[item["title"]] = item

    all_news = list(unique.values())

    # 只保留当天新闻
    final = filter_today(all_news)

    logger.info(f"成功抓取 {len(final)} 条当天新闻")
    return final