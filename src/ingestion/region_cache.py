import json
from pathlib import Path
from datetime import datetime
from src.system.logger import setup_logger

logger = setup_logger("main")

CACHE_PATH = Path("src/data/news_ai/region_cache.jsonl")


def load_region_from_cache(url: str):
    """
    Load region classification result from cache by URL.
    Returns dict with region and reason, or None if not found.
    """
    if not CACHE_PATH.exists():
        logger.info("Region cache file does not exist.")
        return None

    try:
        with CACHE_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    item = json.loads(line)
                    if item.get("url") == url:
                        logger.info(f"Cache hit for region: {url}")
                        return {
                            "region": item.get("region"),
                            "reason": item.get("reason"),
                            "timestamp": item.get("timestamp")
                        }
                except json.JSONDecodeError:
                    logger.warning("Skipping invalid JSON line in region cache.")
                    continue
    except Exception as e:
        logger.error(f"Failed to read region cache: {e}")
        return None

    logger.info(f"No region cache entry found for URL: {url}")
    return None


def save_region_to_cache(url: str, region: str, reason: str):
    """
    Save region classification result to cache.
    Each entry is stored as JSONL with timestamp.
    """
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "url": url,
            "region": region,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }

        with CACHE_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        logger.info(f"Region cached for URL: {url} ({region})")

    except Exception as e:
        logger.error(f"Failed to save region to cache: {e}")