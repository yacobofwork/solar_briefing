import json
from pathlib import Path
from datetime import datetime

CACHE_PATH = Path("data/news_ai/region_cache.jsonl")


def load_region_from_cache(url: str):
    """
    根据 URL 从缓存中读取 region 分类结果
    """
    if not CACHE_PATH.exists():
        return None

    with CACHE_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                item = json.loads(line)
                if item.get("url") == url:
                    return {
                        "region": item.get("region"),
                        "reason": item.get("reason")
                    }
            except:
                continue
    return None


def save_region_to_cache(url: str, region: str, reason: str):
    """
    将 region 分类结果写入缓存
    """
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with CACHE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "url": url,
            "region": region,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False) + "\n")