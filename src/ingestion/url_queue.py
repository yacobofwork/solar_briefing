import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from src.system.logger import setup_logger

logger = setup_logger("url_queue")


QUEUE_FILE = Path("src/data/incoming_urls.jsonl")
QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)


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
                    logger.warning("Skipping invalid JSON line in queue file.")
                    continue

    if url in existing_urls:
        logger.info(f"Duplicate URL ignored: {url}")
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

    logger.info(f"URL enqueued: {url}")
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
                logger.warning("Skipping invalid JSON line in queue file.")
                continue
            if item.get("status") == "pending":
                items.append(item)
    return items


def update_url_status(url: str, status: str) -> None:
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
                logger.warning("Skipping invalid JSON line in queue file.")
                continue
            if item.get("url") == url:
                item["status"] = status
            rows.append(item)

    with QUEUE_FILE.open("w", encoding="utf-8") as f:
        for item in rows:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    logger.info(f"Updated status for {url} → {status}")