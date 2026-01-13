import json
from pathlib import Path

from src.system.config_loader import load_config
from src.system.logger import setup_logger

config = load_config()

docs_datas = Path(config["paths"]["docs_datas"]).resolve()

logger = setup_logger("daily_exporter")


def save_daily_json(
    date_str: str,
    news_html: str,
    news_china_html: str,
    news_nigeria_html: str,
    news_global_html: str,
    price_html: str,
    price_insight_html: str,
    daily_insight_html: str,
    chart_rel_path: str,
) -> None:
    """
    Save a full daily report snapshot for GitHub Pages.
    The JSON will contain all key HTML sections that are already used
    in the email and PDF, so the website can render a page similar to
    the internal daily report.
    """
    try:
        docs_datas.mkdir(parents=True, exist_ok=True)

        data = {
            "date": date_str,
            "news_html": news_html,
            "news_china_html": news_china_html,
            "news_nigeria_html": news_nigeria_html,
            "news_global_html": news_global_html,
            "price_html": price_html,
            "price_insight_html": price_insight_html,
            "daily_insight_html": daily_insight_html,
            "chart_path": chart_rel_path,  # relative path from docs root
        }

        output_file = docs_datas / f"{date_str}.json"
        output_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info(f"Daily JSON saved: {output_file}")

    except Exception as e:
        logger.error(f"Failed to save daily JSON for {date_str}: {e}")


def update_index_json(date_str: str) -> None:
    """
    Update docs/datas/index.json with the new date.
    GitHub Pages will use this index to know which dates are available.
    """
    try:
        index_file = docs_datas / "index.json"
        index_file.parent.mkdir(parents=True, exist_ok=True)

        if index_file.exists():
            try:
                index = json.loads(index_file.read_text(encoding="utf-8"))
            except Exception:
                logger.warning("Index file corrupted, reinitializing.")
                index = {"dates": []}
        else:
            index = {"dates": []}

        # Ensure dates list exists
        if "dates" not in index or not isinstance(index["dates"], list):
            index["dates"] = []

        if date_str not in index["dates"]:
            index["dates"].append(date_str)

        index["dates"] = sorted(set(index["dates"]))

        index_file.write_text(
            json.dumps(index, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info(f"Index updated with date {date_str}")

    except Exception as e:
        logger.error(f"Failed to update index.json with {date_str}: {e}")