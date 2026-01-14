import re
from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup
from src.system.logger import setup_logger

REQUEST_TIMEOUT = 15
logger = setup_logger("main")


@dataclass
class FetchedContent:
    url: str
    source: str          # "wechat" / "web"
    title: str
    html: str
    text: str


def _fetch_html(url: str) -> Optional[str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        logger.info(f"Fetched HTML successfully: {url}")
        return resp.text
    except requests.RequestException as e:
        logger.error(f"Failed to fetch HTML from {url}: {e}")
        return None


def _extract_wechat_content(html: str) -> tuple[str, str]:
    """Extract title and text from WeChat article."""
    soup = BeautifulSoup(html, "html.parser")

    title_el = soup.find(id="activity-name") or soup.find("title")
    title = title_el.get_text(strip=True) if title_el else ""

    content_el = soup.find(id="js_content") or soup.body
    if not content_el:
        return title, ""

    for tag in content_el.find_all(["script", "style"]):
        tag.decompose()

    text = content_el.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{2,}", "\n\n", text)

    return title, text


def _extract_generic_content(html: str) -> tuple[str, str]:
    """Extract title and text from generic web page."""
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
    Fetch HTML and extract main content.
    :param url: Target URL
    :param source: "wechat" or "web"
    :return: FetchedContent or None
    """
    html = _fetch_html(url)
    if not html:
        return None

    try:
        if source == "wechat":
            title, text = _extract_wechat_content(html)
        else:
            title, text = _extract_generic_content(html)

        logger.info(f"Content extracted successfully from {url}")
        return FetchedContent(
            url=url,
            source=source,
            title=title,
            html=html,
            text=text,
        )
    except Exception as e:
        logger.error(f"Failed to extract content from {url}: {e}")
        return None