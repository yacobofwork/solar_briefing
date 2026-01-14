from pathlib import Path
from src.ingestion.url_queue import enqueue_url
from src.system.config_loader import load_config
from src.system.logger import setup_logger

logger = setup_logger("main")

config = load_config()
project_root = Path(__file__).resolve().parents[2]
WECHAT_LINKS_PATH = project_root / config["cache"]["wechat_links_path"]


def read_links_from_file(path: Path = WECHAT_LINKS_PATH) -> list[str]:
    """
    Read all WeChat article URLs from a text file.
    - Skip empty lines
    - Skip invalid URLs
    - Only accept mp.weixin.qq.com links
    """
    if not path.exists():
        logger.warning(f"WeChat link file not found: {path}")
        return []

    links: list[str] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                url = line.strip()
                if not url:
                    continue
                if not url.startswith("https://mp.weixin.qq.com"):
                    logger.info(f"Skipped non-WeChat URL: {url}")
                    continue
                links.append(url)
    except Exception as e:
        logger.error(f"Failed to read WeChat link file {path}: {e}")
        return []

    logger.info(f"Loaded {len(links)} valid WeChat URLs from {path}")
    return links


def ingest_links_to_queue() -> None:
    """
    Read all URLs from wechat_links.txt and enqueue them into incoming_urls.jsonl.
    Duplicate URLs will be ignored by url_queue.enqueue_url().
    """
    logger.info("Starting WeChat link ingestion...")

    links = read_links_from_file()
    if not links:
        logger.info("No valid WeChat article URLs found.")
        return

    for url in links:
        record = enqueue_url(url, source="wechat")
        if record["status"] == "duplicate":
            logger.info(f"Duplicate (skipped): {url}")
        else:
            logger.info(f"Added to queue: {url}")

    logger.info("All links have been written to incoming_urls.jsonl")


if __name__ == "__main__":
    ingest_links_to_queue()