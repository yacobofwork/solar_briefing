# ingestion/url_queue.py
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

QUEUE_FILE = DATA_DIR / "incoming_urls.jsonl"


def _normalize_source(url: str, explicit_source: str | None = None) -> str:
    """
    根据域名推断来源，除非你手动指定：
    - mp.weixin.qq.com -> wechat
    - 其他 -> web
    """
    if explicit_source:
        return explicit_source

    netloc = urlparse(url).netloc.lower()
    if "mp.weixin.qq.com" in netloc:
        return "wechat"
    return "web"


def enqueue_url(url: str, source: str | None = None) -> dict:
    """
    把一个 URL 加入队列（同一 URL 去重）。
    """
    url = url.strip()
    if not url:
        raise ValueError("URL 不能为空")

    src = _normalize_source(url, source)

    existing_urls = set()
    if QUEUE_FILE.exists():
        with QUEUE_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    item = json.loads(line)
                    existing_urls.add(item.get("url"))
                except json.JSONDecodeError:
                    continue

    if url in existing_urls:
        return {
            "url": url,
            "source": src,
            "added_at": None,
            "status": "duplicate",
        }

    record = {
        "url": url,
        "source": src,  # wechat / web
        "added_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "status": "pending",  # pending / fetched / failed
    }

    with QUEUE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record


def load_pending_urls() -> list[dict]:
    """
    读取 status=pending 的 URL。
    """
    if not QUEUE_FILE.exists():
        return []

    items: list[dict] = []
    with QUEUE_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if item.get("status") == "pending":
                items.append(item)
    return items


def update_url_status(url: str, status: str):
    """
    把某个 URL 的 status 更新为 fetched / failed。
    """
    if not QUEUE_FILE.exists():
        return

    rows: list[dict] = []
    with QUEUE_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if item.get("url") == url:
                item["status"] = status
            rows.append(item)

    with QUEUE_FILE.open("w", encoding="utf-8") as f:
        for item in rows:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")