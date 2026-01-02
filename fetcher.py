import requests
from bs4 import BeautifulSoup
from utils import setup_logger

logger = setup_logger("fetcher")


# ============================
# 通用抓取器（增强版）
# ============================
def fetch_from_urls(urls, source, limit=30):
    results = []

    for url in urls:
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            resp.encoding = resp.apparent_encoding
            soup = BeautifulSoup(resp.text, "html.parser")

            for a in soup.select("a"):
                title = a.get_text(strip=True)
                link = a.get("href")

                # 基础过滤
                if not title or not link:
                    continue
                if len(title) < 8:
                    continue
                if any(k in title for k in ["广告", "推广", "热门", "专题", "视频", "直播"]):
                    continue

                # 修复相对链接
                if link.startswith("/"):
                    link = url.rstrip("/") + link

                # 过滤非 http 链接
                if not link.startswith("http"):
                    continue

                results.append({
                    "title": title,
                    "summary": title,
                    "link": link,
                    "source": source
                })

                if len(results) >= limit:
                    break

        except Exception as e:
            logger.warning(f"抓取失败：{url} - {e}")

    return results


# ============================
# PV 新闻
# ============================
def fetch_pv_news():
    urls = [
        "https://guangfu.bjx.com.cn/",
        "https://www.solarbe.com/",
        "https://www.pv-tech.org/category/china/",
        "https://www.pvmen.com/"
    ]
    return fetch_from_urls(urls, source="PV", limit=30)


# ============================
# BESS 新闻
# ============================
def fetch_bess_news():
    urls = [
        "https://chuneng.bjx.com.cn/",
        "https://www.escn.com.cn/",
        "https://www.eesa.org.cn/"
    ]
    return fetch_from_urls(urls, source="BESS", limit=30)


# ============================
# Policy 新闻
# ============================
def fetch_policy_news():
    urls = [
        "https://www.nea.gov.cn/",
        "https://www.cls.cn/energy",
        "https://www.stcn.com/energy/"
    ]
    return fetch_from_urls(urls, source="Policy", limit=30)


# ============================
# 高质量来源：财联社
# ============================
def fetch_cailian():
    url = "https://www.cls.cn/theme/1033"
    items = []

    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
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


# ============================
# 高质量来源：36Kr
# ============================
def fetch_36kr():
    url = "https://36kr.com/information/web_news/energy"
    items = []

    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
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


# ============================
# 高质量来源：搜狐能源
# ============================
def fetch_sohu_energy():
    url = "https://business.sohu.com/energy/"
    items = []

    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
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


# ============================
# 合并所有新闻（最终接口）
# ============================
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

    final = list(unique.values())

    logger.info(f"成功抓取 {len(final)} 条新闻")
    return final