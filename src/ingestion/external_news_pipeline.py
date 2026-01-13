import datetime
from typing import List, Dict

from src.system.logger import setup_logger
from src.modules.insights_core import safe_ai_summary_industry
from src.ingestion.ai_cache import load_summary_from_cache, save_summary_to_cache
from src.ingestion.region_cache import load_region_from_cache, save_region_to_cache
from src.ingestion.url_queue import load_pending_urls, update_url_status
from src.ingestion.content_fetcher import fetch_and_extract
from src.ingestion.region_classifier import classify_region_ai
from src.ingestion.url_queue_cleanup import cleanup_url_queue

logger = setup_logger("external_news_pipeline")


def process_pending_urls_to_raw_news() -> List[Dict]:
    """
    Convert pending URLs in the queue into raw news items.
    Output fields align with fetch_all_news():
      - title
      - summary
      - source
      - link
      - pub_date
      - region
    """
    pending = load_pending_urls()
    if not pending:
        logger.info("No pending URLs, skipping.")
        return []

    today_str = datetime.date.today().isoformat()
    results: List[Dict] = []

    for record in pending:
        url = record.get("url")
        source = record.get("source", "web")  # default to web
        logger.info(f"Processing URL: {url} (source={source})")

        # Fetch content
        fetched = fetch_and_extract(url, source)
        if not fetched or not fetched.text.strip():
            logger.warning(f"Failed to fetch or empty content: {url}")
            update_url_status(url, "failed")
            continue

        # Summary (cached or AI)
        summary = load_summary_from_cache(url)
        if summary:
            logger.info(f"Loaded summary from cache for {url}")
        else:
            try:
                summary = safe_ai_summary_industry(fetched.text)
                save_summary_to_cache(url, summary)
                logger.info(f"Generated and cached summary for {url}")
            except Exception as e:
                logger.error(f"Failed to generate summary for {url}: {e}")
                update_url_status(url, "failed")
                continue

        # Region classification (cached or AI)
        cached_region = load_region_from_cache(url)
        if cached_region:
            region = cached_region.get("region", "global")
            reason = cached_region.get("reason", "")
            logger.info(f"Loaded region from cache for {url}: {region}")
        else:
            try:
                region_json = classify_region_ai(
                    title=fetched.title,
                    summary=summary,
                    link=url,
                    raw_text=fetched.text
                )
                region = region_json.get("region", "global")
                reason = region_json.get("reason", "")
                save_region_to_cache(url, region, reason)
                logger.info(f"Classified region for {url}: {region}")
            except Exception as e:
                logger.error(f"Failed to classify region for {url}: {e}")
                region = "global"

        # Build news item
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

    logger.info(f"Generated {len(results)} external news items.")

    # Cleanup queue
    cleanup_url_queue()
    return results