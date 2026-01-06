# daily_exporter.py

import json
from pathlib import Path


def save_daily_json(date_str, summary, insights, articles):
    """
    Save daily intelligence data to docs/data/YYYY-MM-DD.json
    This file will be used by GitHub Pages to display daily intelligence.
    """
    base = Path(__file__).resolve().parent.parent / "docs" / "data"
    base.mkdir(parents=True, exist_ok=True)

    data = {
        "summary": summary,
        "insights": insights,
        "articles": articles,
    }

    with open(base / f"{date_str}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def update_index_json(date_str):
    """
    Update docs/data/index.json with the new date.
    GitHub Pages uses this file to know which dates exist.
    """
    index_file = Path(__file__).resolve().parent.parent / "docs" / "data" / "index.json"
    index_file.parent.mkdir(parents=True, exist_ok=True)

    if index_file.exists():
        index = json.loads(index_file.read_text(encoding="utf-8"))
    else:
        index = {"dates": []}

    if date_str not in index["dates"]:
        index["dates"].append(date_str)

    index["dates"].sort()

    index_file.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")