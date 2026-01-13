import json
from pathlib import Path
from datetime import datetime
from src.system.logger import setup_logger

logger = setup_logger("ai_cache")

CACHE_PATH = Path("src/data/news_ai/summary_cache.jsonl")


def load_summary_from_cache(url: str):
    """
    Load cached summary for a given URL.
    Returns None if not found or cache file missing.
    """
    if not CACHE_PATH.exists():
        logger.info("Cache file does not exist.")
        return None

    try:
        with CACHE_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    item = json.loads(line)
                    if item.get("url") == url:
                        logger.info(f"Cache hit for URL: {url}")
                        return item.get("summary")
                except json.JSONDecodeError:
                    logger.warning("Skipping invalid JSON line in cache.")
                    continue
    except Exception as e:
        logger.error(f"Failed to read cache file: {e}")
        return None

    logger.info(f"No cache entry found for URL: {url}")
    return None


def save_summary_to_cache(url: str, summary: str, source: str = None):
    """
    Save summary to cache file.
    Each entry is stored as JSONL with timestamp.
    """
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "url": url,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
        if source:
            entry["source"] = source

        with CACHE_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        logger.info(f"Summary cached for URL: {url}")

    except Exception as e:
        logger.error(f"Failed to save summary to cache: {e}")