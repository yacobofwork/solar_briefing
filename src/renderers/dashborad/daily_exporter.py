# renderers/daily_exporter.py

import json
from pathlib import Path


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
    base = Path(__file__).resolve().parent.parent / "docs" / "datas"
    base.mkdir(parents=True, exist_ok=True)

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

    output_file = base / f"{date_str}.json"
    output_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def update_index_json(date_str: str) -> None:
    """
    Update docs/data/index.json with the new date.
    GitHub Pages will use this index to know which dates are available.
    """
    index_file = Path(__file__).resolve().parent.parent / "docs" / "datas" / "index.json"
    index_file.parent.mkdir(parents=True, exist_ok=True)

    if index_file.exists():
        index = json.loads(index_file.read_text(encoding="utf-8"))
    else:
        index = {"dates": []}

    if date_str not in index["dates"]:
        index["dates"].append(date_str)

    index["dates"].sort()
    index_file.write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )