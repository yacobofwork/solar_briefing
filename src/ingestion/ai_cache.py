import json
from pathlib import Path
from datetime import datetime


CACHE_PATH = Path("data/news_ai/summary_cache.jsonl")


def load_summary_from_cache(url: str):
    if not CACHE_PATH.exists():
        return None

    with CACHE_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                item = json.loads(line)
                if item.get("url") == url:
                    return item.get("summary")
            except:
                continue
    return None


def save_summary_to_cache(url: str, summary: str):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with CACHE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "url": url,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False) + "\n")