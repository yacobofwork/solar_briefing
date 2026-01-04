# ingestion/external_news_pipeline.py
import datetime
from typing import List, Dict

from .url_queue import load_pending_urls, update_url_status
from .content_fetcher import fetch_and_extract


def _simple_summary(text: str, max_chars: int = 500) -> str:
    """
    暂时用纯截断做“摘要”，不引入 AI，保证零胡编。
    将来你要换成保真 AI 摘要，只需要替换这里。
    """
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def process_pending_urls_to_raw_news() -> List[Dict]:
    """
    把队列中 pending 的 URL 变成“原始新闻条目”，
    字段对齐 fetch_all_news() 的输出结构：
      - title
      - summary
      - source
      - link
      - pub_date
      - region
    """
    pending = load_pending_urls()
    if not pending:
        print("[external_news] 没有 pending URL，跳过。")
        return []

    today_str = datetime.date.today().isoformat()
    results: List[Dict] = []

    for record in pending:
        url = record["url"]
        source = record["source"]   # wechat / web
        print(f"[external_news] 处理 URL: {url} ({source})")

        fetched = fetch_and_extract(url, source)
        if not fetched or not fetched.text.strip():
            update_url_status(url, "failed")
            continue

        summary = _simple_summary(fetched.text)

        news_item = {
            "title": fetched.title or url,
            "summary": summary,
            "source": "WeChat" if source == "wechat" else "External",
            "link": url,
            "pub_date": today_str,
            # 暂时统一归为 global，后面你可以按关键词/域名再细化到 china/nigeria
            "region": "global",
        }
        results.append(news_item)

        update_url_status(url, "fetched")

    print(f"[external_news] 本次共生成 {len(results)} 条外部新闻。")
    return results