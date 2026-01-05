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
    Infer the source type based on domain unless explicitly provided.
    - mp.weixin.qq.com -> wechat
    - everything else -> web
    """
    if explicit_source:
        return explicit_source

    netloc = urlparse(url).netloc.lower()
    if "mp.weixin.qq.com" in netloc:
        return "wechat"
    return "web"


def enqueue_url(url: str, source: str | None = None) -> dict:
    """
    Add a URL into the queue (deduplicated).
    Returns a record with status:
    - pending
    - duplicate
    """
    url = url.strip()
    if not url:
        raise ValueError("URL cannot be empty")

    src = _normalize_source(url, source)

    # Load existing URLs to avoid duplicates
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
        "source": src,
        "added_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "status": "pending",  # pending / fetched / failed
    }

    with QUEUE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record


def load_pending_urls() -> list[dict]:
    """
    Load all URLs with status = 'pending'.
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
    Update the status of a specific URL:
    - fetched
    - failed
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