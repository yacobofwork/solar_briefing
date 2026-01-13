# ingestion/external_news_pipeline.py
import datetime
from typing import List, Dict

from solar_intel_v2.modules.insights_core import safe_ai_summary_industry
from solar_intel_v2.ingestion.ai_cache import load_summary_from_cache, save_summary_to_cache
from solar_intel_v2.ingestion.region_cache import load_region_from_cache, save_region_to_cache
from solar_intel_v2.ingestion.url_queue import load_pending_urls, update_url_status
from solar_intel_v2.ingestion.content_fetcher import fetch_and_extract
from solar_intel_v2.ingestion.region_classifier import classify_region_ai
from solar_intel_v2.ingestion.url_queue_cleanup import cleanup_url_queue


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

        cached = load_summary_from_cache(url)
        if cached:
            summary = cached
        else:
            # summary = safe_ai_summary(fetched.text)
            summary = safe_ai_summary_industry(fetched.text)
            save_summary_to_cache(url,summary)

        # 将消息进行 region 分类
        cached_region = load_region_from_cache(url)
        if cached_region:
            region = cached_region["region"]
            reason = cached_region["reason"]
        else:
            region_json = classify_region_ai(
                title=fetched.title,
                summary=summary,
                link=url,
                raw_text=fetched.text
            )
            region = region_json.get("region","global")
            reason = region_json.get("reason","")
            save_region_to_cache(url,region,reason)

        news_item = {
            "title": fetched.title or url,
            "summary": summary,
            "source": "WeChat" if source == "wechat" else "External",
            "link": url,
            "pub_date": today_str,
            "region": region,
        }
        results.append(news_item)

        update_url_status(url, "fetched")

    print(f"[external_news] 本次共生成 {len(results)} 条外部新闻。")

    # 进行队列自动清理
    cleanup_url_queue()
    return results