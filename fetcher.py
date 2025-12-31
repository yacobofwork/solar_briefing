import requests
from bs4 import BeautifulSoup
from utils import setup_logger

logger = setup_logger("fetcher")

# 光伏抓取函数
def fetch_pv_news():
    urls = [
        "https://guangfu.bjx.com.cn/",
        "https://www.solarbe.com/",
        "https://www.pv-tech.org/category/china/",
        "https://www.pvmen.com/"
    ]
    return fetch_from_urls(urls, source="PV")

# 储能抓取函数
def fetch_bess_news():
    urls = [
        "https://chuneng.bjx.com.cn/",
        "https://www.escn.com.cn/",
        "https://www.eesa.org.cn/",
    ]
    return fetch_from_urls(urls, source="BESS")

# 政策/供应链抓取函数
def fetch_policy_news():
    urls = [
        "https://www.nea.gov.cn/",
        "https://www.cls.cn/energy",
        "https://www.stcn.com/energy/"
    ]
    return fetch_from_urls(urls, source="Policy")

def fetch_all_news():
    news = []
    news.extend(fetch_pv_news())
    news.extend(fetch_bess_news())
    news.extend(fetch_policy_news())
    return news

import requests
from bs4 import BeautifulSoup

def fetch_from_urls(urls, source):
    """通用抓取函数：从多个 URL 抓取新闻标题和链接"""
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    results = []

    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.encoding = resp.apparent_encoding
            soup = BeautifulSoup(resp.text, "html.parser")

            # 通用标题选择器（适配大部分新闻站）
            candidates = soup.select("a")  # 抓取所有链接

            for a in candidates:
                title = a.get_text(strip=True)
                link = a.get("href")

                # 过滤无效内容
                if not title or not link:
                    continue
                if len(title) < 6:  # 避免“更多”“点击”等垃圾标题
                    continue

                # 修复相对链接
                if link.startswith("/"):
                    link = url.rstrip("/") + link

                results.append({
                    "title": title,
                    "link": link,
                    "source": source
                })

        except Exception as e:
            print(f"[WARN] 抓取失败：{url} - {e}")
            continue

    # 去重
    unique = []
    seen = set()
    for item in results:
        if item["title"] not in seen:
            seen.add(item["title"])
            unique.append(item)

    return unique

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