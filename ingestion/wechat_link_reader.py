# ingestion/wechat_link_reader.py

from pathlib import Path
from .url_queue import enqueue_url

BASE_DIR = Path(__file__).resolve().parent.parent
LINK_FILE = BASE_DIR / "wechat_links.txt"


def read_links_from_file(path=LINK_FILE) -> list[str]:
    """
    Read all WeChat article URLs from a text file.
    - Skip empty lines
    - Skip invalid URLs
    - Only accept mp.weixin.qq.com links
    """
    if not path.exists():
        print(f"File not found: {path}")
        return []

    links: list[str] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            url = line.strip()
            if not url:
                continue
            if not url.startswith("https://mp.weixin.qq.com"):
                print(f"Skipped non-WeChat URL: {url}")
                continue
            links.append(url)

    return links


def ingest_links_to_queue():
    """
    Read all URLs from wechat_links.txt and enqueue them into incoming_urls.jsonl.
    Duplicate URLs will be ignored by url_queue.enqueue_url().
    """
    print("Starting WeChat link ingestion...")

    links = read_links_from_file()
    if not links:
        print("No valid WeChat article URLs found.")
        return

    print(f"Loaded {len(links)} WeChat article URLs\n")

    for url in links:
        record = enqueue_url(url, source="wechat")
        if record["status"] == "duplicate":
            print(f"Duplicate (skipped): {url}")
        else:
            print(f"Added to queue: {url}")

    print("\n🎉 All links have been written to incoming_urls.jsonl")


if __name__ == "__main__":
    ingest_links_to_queue()