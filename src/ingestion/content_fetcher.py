# ingestion/content_fetcher.py
import re
from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup  # 记得在 requirements.txt 里加 beautifulsoup4

REQUEST_TIMEOUT = 15


@dataclass
class FetchedContent:
    url: str
    source: str          # wechat / web
    title: str
    html: str
    text: str


def _fetch_html(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text


def _extract_wechat_content(html: str) -> tuple[str, str]:
    """
    微信文章：title + #js_content
    """
    soup = BeautifulSoup(html, "html.parser")

    title_el = soup.find(id="activity-name")
    if not title_el:
        title_el = soup.find("title")
    title = title_el.get_text(strip=True) if title_el else ""

    content_el = soup.find(id="js_content")
    if not content_el:
        content_el = soup.body

    if not content_el:
        return title, ""

    for tag in content_el.find_all(["script", "style"]):
        tag.decompose()

    text = content_el.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{2,}", "\n\n", text)

    return title, text


def _extract_generic_content(html: str) -> tuple[str, str]:
    """
    普通网页：title + <article>/<main>/body
    """
    soup = BeautifulSoup(html, "html.parser")

    title_el = soup.find("title")
    title = title_el.get_text(strip=True) if title_el else ""

    content_el = (
        soup.find("article")
        or soup.find("main")
        or soup.find("div", {"id": "content"})
        or soup.body
    )

    if not content_el:
        return title, ""

    for tag in content_el.find_all(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = content_el.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{2,}", "\n\n", text)

    return title, text


def fetch_and_extract(url: str, source: str) -> Optional[FetchedContent]:
    """
    抓取并抽取正文。
    """
    try:
        html = _fetch_html(url)
    except Exception as e:
        print(f"[content_fetcher] 抓取失败: {url} ({e})")
        return None

    if source == "wechat":
        title, text = _extract_wechat_content(html)
    else:
        title, text = _extract_generic_content(html)

    return FetchedContent(
        url=url,
        source=source,
        title=title,
        html=html,
        text=text,
    )