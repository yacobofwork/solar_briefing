import requests
from bs4 import BeautifulSoup
from utils import setup_logger

logger = setup_logger("fetcher")


def fetch_cailian():
    """财联社新能源主题"""
    url = "https://www.cls.cn/theme/1033"
    headers = {"User-Agent": "Mozilla/5.0"}
    items = []

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        for div in soup.select(".theme-news-list .theme-news-item")[:10]:
            title = div.select_one(".theme-news-title").get_text(strip=True)
            link = "https://www.cls.cn" + div.select_one("a").get("href")
            summary = div.select_one(".theme-news-content").get_text(strip=True)

            items.append({
                "title": title,
                "summary": summary,
                "link": link,
                "source": "财联社"
            })

    except Exception as e:
        logger.error(f"财联社抓取失败: {e}")

    return items


def fetch_36kr():
    """36Kr 新能源"""
    url = "https://36kr.com/information/web_news/energy"
    headers = {"User-Agent": "Mozilla/5.0"}
    items = []

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        for div in soup.select(".information-flow-item")[:10]:
            a = div.find("a")
            if not a:
                continue

            title = a.get_text(strip=True)
            link = "https://36kr.com" + a.get("href")
            summary = div.get_text(strip=True)

            items.append({
                "title": title,
                "summary": summary,
                "link": link,
                "source": "36Kr"
            })

    except Exception as e:
        logger.error(f"36Kr 抓取失败: {e}")

    return items


def fetch_sohu_energy():
    """搜狐能源频道"""
    url = "https://business.sohu.com/energy/"
    headers = {"User-Agent": "Mozilla/5.0"}
    items = []

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        for li in soup.select(".news-box li")[:10]:
            a = li.find("a")
            if not a:
                continue

            title = a.get_text(strip=True)
            link = a.get("href")
            summary = li.get_text(strip=True)

            items.append({
                "title": title,
                "summary": summary,
                "link": link,
                "source": "搜狐能源"
            })

    except Exception as e:
        logger.error(f"搜狐能源抓取失败: {e}")

    return items


def fetch_all_news():
    logger.info("开始抓取新闻…")

    items = []
    items += fetch_cailian()
    items += fetch_36kr()
    items += fetch_sohu_energy()

    # 去重
    unique = {}
    for item in items:
        if item["title"] not in unique:
            unique[item["title"]] = item

    final = list(unique.values())

    if not final:
        logger.error("未获取到任何新闻")
    else:
        logger.info(f"成功抓取 {len(final)} 条新闻")

    return final