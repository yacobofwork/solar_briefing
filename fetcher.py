import datetime
import re
import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser
from utils import setup_logger

logger = setup_logger("fetcher")


# ============================================================
# 统一日期解析模块
# ============================================================
def parse_date(text):
    """统一解析各种新闻日期格式，返回 datetime.date"""

    if not text:
        return datetime.date.today()  # fallback：没有日期 → 默认今天

    text = text.strip()
    today = datetime.date.today()
    now = datetime.datetime.now()

    # -------------------------
    # 相对时间
    # -------------------------
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

    # -------------------------
    # 财联社格式：10:33 → 默认今天
    # -------------------------
    if re.match(r"^\d{1,2}:\d{2}$", text):
        return today

    # -------------------------
    # 中文日期：2025年01月02日
    # -------------------------
    m = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text)
    if m:
        y, mth, d = map(int, m.groups())
        return datetime.date(y, mth, d)

    # -------------------------
    # 常见格式：2025-01-02 / 2025/01/02 / 2025-01-02 10:33
    # -------------------------
    try:
        dt = parser.parse(text)
        return dt.date()
    except:
        pass

    # -------------------------
    # fallback：无法解析 → 默认今天
    # -------------------------
    return today


# ============================================================
# 过滤当天新闻
# ============================================================
def filter_today(news_list):
    today = datetime.date.today()
    return [item for item in news_list if item.get("pub_date") == today]


# ============================================================
# 新闻源 1：PV-Tech（RSS）
# ============================================================
def fetch_pv_news():
    url = "https://www.pv-tech.org/feed/"
    items = []

    try:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            pub = parser.parse(entry.published).date()

            items.append({
                "title": entry.title,
                "link": entry.link,
                "summary": entry.get("summary", ""),
                "pub_date": pub
            })
    except Exception as e:
        logger.error(f"PV-Tech 抓取失败：{e}")

    return items


# ============================================================
# 新闻源 2：Energy-Storage（RSS）
# ============================================================
def fetch_bess_news():
    url = "https://www.energy-storage.news/feed/"
    items = []

    try:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            pub = parser.parse(entry.published).date()

            items.append({
                "title": entry.title,
                "link": entry.link,
                "summary": entry.get("summary", ""),
                "pub_date": pub
            })
    except Exception as e:
        logger.error(f"BESS 新闻抓取失败：{e}")

    return items


# ============================================================
# 新闻源 3：北极星政策（RSS）
# ============================================================
def fetch_policy_news():
    url = "https://www.ne21.com/rss/"
    items = []

    try:
        feed = feedparser.parse(url)

        if not feed.entries:
            logger.warning("政策 RSS 无数据，可能被阻断")
            return []

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
        logger.error(f"政策 RSS 抓取失败：{e}")

    return items


# ============================================================
# 新闻源 4：财联社（HTML）
# ============================================================
def fetch_cailian():
    url = "https://www.cls.cn/v/energy"
    items = []

    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        for div in soup.select(".timeline-item"):
            title = div.select_one(".title").get_text(strip=True)
            link = div.select_one("a")["href"]
            time_text = div.select_one(".time").get_text(strip=True)

            pub = parse_date(time_text)

            items.append({
                "title": title,
                "link": link,
                "summary": "",
                "pub_date": pub
            })

    except Exception as e:
        logger.error(f"财联社抓取失败：{e}")

    return items


# ============================================================
# 新闻源 5：36Kr（HTML）
# ============================================================
def fetch_36kr():
    url = "https://36kr.com/information/web_news"
    items = []

    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        for div in soup.select(".kr-flow-feed"):
            title = div.select_one(".title").get_text(strip=True)
            link = "https://36kr.com" + div.select_one("a")["href"]
            time_text = div.select_one(".time").get_text(strip=True)

            pub = parse_date(time_text)

            items.append({
                "title": title,
                "link": link,
                "summary": "",
                "pub_date": pub
            })

    except Exception as e:
        logger.error(f"36Kr 抓取失败：{e}")

    return items


# ============================================================
# 新闻源 6：搜狐能源（HTML）
# ============================================================
def fetch_sohu_energy():
    url = "https://www.sohu.com/c/8/1460"
    items = []

    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        for div in soup.select(".news-box"):
            title = div.select_one("h4").get_text(strip=True)
            link = "https://www.sohu.com" + div.select_one("a")["href"]
            time_text = div.select_one(".time").get_text(strip=True)

            pub = parse_date(time_text)

            items.append({
                "title": title,
                "link": link,
                "summary": "",
                "pub_date": pub
            })

    except Exception as e:
        logger.error(f"搜狐能源抓取失败：{e}")

    return items


# ============================================================
# 主函数：抓取所有新闻 + 去重 + 当天过滤
# ============================================================
def fetch_all_news():
    logger.info("开始抓取新闻…")

    items = []
    items += fetch_pv_news()
    items += fetch_bess_news()
    items += fetch_policy_news()

    items += fetch_cailian()
    items += fetch_36kr()
    items += fetch_sohu_energy()

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