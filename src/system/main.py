import os
import shutil
import datetime
import subprocess
from pathlib import Path

from src.renderers.dashborad.article_renderer import render_article
from src.renderers.dashborad.daily_exporter import save_daily_json, update_index_json
from src.renderers.dashborad.insight_renderer import render_daily_insight
from src.renderers.dashborad.price_renderer import render_price_insight
from src.system.logger import setup_logger
from src.system.cache_manager import DailyCache

from src.ingestion.fetch_prices import fetch_all_prices
from src.ingestion.fetcher import fetch_all_news
from src.ingestion.save_price_history import save_price_history
from src.ingestion.external_news_pipeline import process_pending_urls_to_raw_news

from src.renderers.charts.chart_builder import build_price_chart
from src.renderers.pdf.pdf_builder import build_pdf
from src.renderers.email.email_sender import send_email
from src.system.config_loader import load_config

from src.modules.insights_core import (
    summarize_article,
    analyze_price_impact,
    generate_daily_insight,
    generate_price_trend_chart   # ← 新增这一行
)

# ============================================================
# Init configuration and logger
# ============================================================


config = load_config()

logger = setup_logger("main",config)

project_root = Path(__file__).resolve().parents[2]
cache = DailyCache(project_root / config["cache"]["path"])
history_file_path = project_root / config["paths"]["history_file_path"]
docs_dir = project_root / "docs/"

cache_enabled = config["cache"]["enabled"]
cache.clean_old_cache(config["cache"]["keep_days"])
charts_dir = config["paths"]["charts_dir"]


# ============================================================
# 1. Data fetching
# ============================================================

def fetch_data():
    if cache_enabled and cache.exists("prices"):
        logger.info("Loading prices from cache...")
        price_list = cache.load("prices")
    else:
        logger.info("Fetching price data...")
        price_list = fetch_all_prices()
        if cache_enabled:
            cache.save("prices", price_list)

    if cache_enabled and cache.exists("news_raw"):
        logger.info("Loading raw news from cache...")
        news_list = cache.load("news_raw")
    else:
        logger.info("Fetching news data...")
        news_list = fetch_all_news()
        if cache_enabled:
            cache.save("news_raw", news_list)

    logger.info("Processing external URL queue for additional news...")
    external_news = process_pending_urls_to_raw_news()
    if external_news:
        logger.info(f"Added {len(external_news)} external news items.")
        news_list.extend(external_news)
        if cache_enabled:
            cache.save("news_raw", news_list)

    return price_list, news_list


# ============================================================
# 2. AI processing
# ============================================================

def process_news_ai(news_list):
    # If no news passed in, skip DS call
    if not news_list:
        logger.info("No news data provided, skipping AI processing.")
        return []

    # If cache exists, load from cache
    if cache_enabled and cache.exists("news_ai"):
        logger.info("Loading AI-processed news from cache...")
        return cache.load("news_ai")

    logger.info("Processing news with AI...")
    results = []
    for item in news_list:
        article_obj = {
            "summary": item.get("summary", item.get("title")),
            "source": item.get("source", "Unknown"),
            "link": item.get("link"),
            "pub_date": item.get("pub_date")
        }
        ai_json = summarize_article(article_obj)
        results.append(ai_json)

    if cache_enabled:
        cache.save("news_ai", results)

    return results


def process_price_ai(price_list, date):
    if cache_enabled and cache.exists("price_insight"):
        logger.info("Loading price insight from cache...")
        price_insight = cache.load("price_insight")
    else:
        raw_price_insight = analyze_price_impact(price_list)
        price_insight = render_price_insight(raw_price_insight)
        if cache_enabled:
            cache.save("price_insight", price_insight)


    os.makedirs(charts_dir, exist_ok=True)
    filename = f"price_chart_{date}.png"
    chart_abs_path = os.path.abspath(os.path.join(charts_dir, filename))

    if cache_enabled and os.path.exists(chart_abs_path):
        logger.info("Using cached chart...")
    else:
        logger.info("Generating price chart...")
        build_price_chart(history_file_path, chart_abs_path)

    chart_rel_for_docs = f"charts/{filename}"
    return chart_abs_path, chart_rel_for_docs, price_insight


# ============================================================
# 2.5 Raw Material Trend Chart (NEW)
# ============================================================

def generate_and_save_raw_material_chart(date: str, cache_enabled: bool = False) -> tuple[str | None, str | None]:
    """
    Generate raw material price trend chart via AI web search and save to file.

    Returns:
        tuple: (base64_string, file_path) — both may be None if failed
    """
    import base64
    from pathlib import Path

    # Try cache first
    if cache_enabled and cache.exists("raw_material_chart"):
        logger.info("Loading raw material trend chart from cache...")
        raw_material_chart_b64 = cache.load("raw_material_chart")
    else:
        logger.info("Generating raw material price trend chart via AI web search...")
        raw_material_chart_b64 = generate_price_trend_chart()
        if cache_enabled:
            cache.save("raw_material_chart", raw_material_chart_b64)

    if not raw_material_chart_b64:
        logger.warning("No chart data returned from AI.")
        return None, None

    # Save to file
    try:
        chart_dir = Path(config["paths"]["charts_dir"]).resolve()
        chart_dir.mkdir(exist_ok=True)
        filename = f"raw_material_trend_{date}.png"
        chart_path = str(chart_dir / filename)

        with open(chart_path, "wb") as f:
            f.write(base64.b64decode(raw_material_chart_b64))
        logger.info(f"Raw material trend chart saved: {chart_path}")
        return raw_material_chart_b64, chart_path

    except Exception as e:
        logger.error(f"Failed to save raw material chart: {e}")
        return raw_material_chart_b64, None

# ============================================================
# 3. Region grouping
# ============================================================

def group_news_by_region(results):
    if cache_enabled and cache.exists("china"):
        logger.info("Loading region groups from cache...")
        return cache.load("china"), cache.load("nigeria"), cache.load("global")

    china = [r for r in results if r.get("region") == "china"]
    nigeria = [r for r in results if r.get("region") == "nigeria"]
    global_news = [r for r in results if r.get("region") == "global"]

    if cache_enabled:
        cache.save("china", china)
        cache.save("nigeria", nigeria)
        cache.save("global", global_news)

    return china, nigeria, global_news


# ============================================================
# 4. Rendering
# ============================================================

def render_news_sections(china, nigeria, global_news):
    html = ""
    if china:
        html += "<h2>China Supply Chain</h2>"
        html += "".join(render_article(item) for item in china)
    if nigeria:
        html += "<h2>Nigeria Market</h2>"
        html += "".join(render_article(item) for item in nigeria)
    if global_news:
        html += "<h2>Global Solar & Storage</h2>"
        html += "".join(render_article(item) for item in global_news)
    return html


def render_pdf_sections(china, nigeria, global_news):
    return (
        "".join(render_article(n) for n in china),
        "".join(render_article(n) for n in nigeria),
        "".join(render_article(n) for n in global_news),
    )


def render_price_table(price_list):
    if not price_list:
        return "<p>No price data available today.</p >"
    rows = "".join(
        f"<tr><td>{p['item']}</td><td>{p['price']}</td><td>{p['change']}</td><td>{p['source']}</td></tr>"
        for p in price_list
    )
    return f"<table><tr><th>Item</th><th>Price</th><th>Change</th><th>Source</th></tr>{rows}</table>"


# ============================================================
# 5. Output (PDF + Email)
# ============================================================

def export_pdf(date, news_html, news_china, news_nigeria, news_global,
               price_html, chart_path, price_insight, daily_insight):

    pdf_dir = Path(config["paths"]["pdf_dir"]).resolve()
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.abspath(os.path.join(pdf_dir, f"daily_report_{date}.pdf"))

    logo_path = Path(config["paths"]["logo_path"]).resolve()

    build_pdf(
        news_html=news_html,
        news_china=news_china,
        news_nigeria=news_nigeria,
        news_global=news_global,
        price_html=price_html,
        chart_path=chart_path,
        date=date,
        price_insight=price_insight,
        daily_insight=daily_insight,
        logo_path=logo_path,
        output_path=pdf_path
    )

    if pdf_path and os.path.exists(pdf_path):
        archive_dir = Path(config["paths"]["archive_dir"]).resolve()
        os.makedirs(archive_dir, exist_ok=True)
        shutil.copy(pdf_path, os.path.join(archive_dir, f"daily_report_{date}.pdf"))
        logger.info(f"PDF archiving successfully to : {pdf_path}")
    else:
        logger.error("PDF not generated, skip archiving")


    return pdf_path


def send_daily_email(news_china, news_nigeria, news_global,
                     news_html, price_html, price_insight,
                     daily_insight, chart_path, date, pdf_path):
    success = send_email(
        news_china=news_china,
        news_nigeria=news_nigeria,
        news_global=news_global,
        news_html=news_html,
        price_html=price_html,
        price_insight=price_insight,
        daily_insight=daily_insight,
        chart_path=chart_path,
        date=date,
        pdf_path=pdf_path
    )

    if success:
        safe_delete(pdf_path)
        logger.info("Email sent successfully")
    else:
        logger.error("Email sending failed")


def safe_delete(path):
    try:
        if os.path.exists(path):
            os.remove(path)
            return True
    except Exception as e:
        logger.error(f"Failed to delete {path}: {e}")
    return False


def git_push():
    try:
        subprocess.run(["git", "add", f"{docs_dir}"], check=True)
        subprocess.run(["git", "commit", "-m", "Daily data update"], check=True)
        subprocess.run(["git", "push", "origin", "master"], check=True)
        logger.info("GitHub push completed.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Git push failed: {e}")


# ============================================================
# Main pipeline
# ============================================================
# ============================================================
# Main pipeline
# ============================================================

def run():
    logger.info("=== Saba Energy Intelligence System starting ===")

    # Step 1: Fetch data
    price_list, news_list = fetch_data()
    save_price_history(price_list, history_file_path)

    # Step 2: AI process news
    ai_results = process_news_ai(news_list)

    # Step 3: Group by region
    china_news, nigeria_news, global_news = group_news_by_region(ai_results)

    # Step 4: Date
    date = datetime.date.today().strftime("%Y-%m-%d")

    # Step 5: Price processing
    chart_path, chart_rel_for_docs, price_insight = process_price_ai(price_list, date)

    # Copy chart to docs/charts for GitHub Pages
    docs_charts_dir = Path(config["paths"]["docs_charts"]).resolve()
    os.makedirs(docs_charts_dir, exist_ok=True)
    if chart_path and os.path.exists(chart_path):
        shutil.copy(chart_path, os.path.join(docs_charts_dir, f"price_chart_{date}.png"))
        logger.info(f"Price chart copied to docs : {docs_charts_dir}")
    else:
        logger.warning("Price chart not generated, skip copying to docs")

    # Step 6: Render HTML
    news_html = render_news_sections(china_news, nigeria_news, global_news)
    news_china, news_nigeria, news_global = render_pdf_sections(china_news, nigeria_news, global_news)
    price_html = render_price_table(price_list)

    # Step 7: Daily Insight
    if cache_enabled and cache.exists("daily_insight"):
        logger.info("Loading daily insight from cache...")
        daily_insight = cache.load("daily_insight")
    else:
        raw_daily_insight = generate_daily_insight()
        daily_insight = render_daily_insight(raw_daily_insight)
        if cache_enabled:
            cache.save("daily_insight", daily_insight)

    with open("email_debug.html", "w") as f:
        f.write(f"<html><body>{daily_insight}</body></html>")

    # Step 7.5: Generate raw material trend chart (NEW - single function call)
    raw_material_chart_b64, raw_material_chart_path = generate_and_save_raw_material_chart(date, cache_enabled)
    logger.info(f"Base64 length: {len(raw_material_chart_b64)}")

    # Inject chart into daily_insight as inline HTML (no need to change PDF/email functions)
    if raw_material_chart_b64:
        chart_html = f'''
        <div style="margin: 30px 0; page-break-before: always;">
            <h2>Core Raw Material Price Trends (Last 7 Days)</h2>
            <img src="data:image/png;base64,{raw_material_chart_b64}" 
                 alt="PV & BESS Raw Material Trends"
                 style="max-width: 100%; height: auto; border: 1px solid #eee; border-radius: 8px;">
            <p style="font-size: 0.9em; color: #666; margin-top: 8px;">
                Data sourced via real-time web search on {date}.
            </p>
        </div>
        '''
        daily_insight += chart_html
    else:
        daily_insight += "<p><em>Raw material trend chart could not be generated.</em></p>"

    # Step 8: PDF output
    pdf_path = export_pdf(
        date, news_html, news_china, news_nigeria, news_global,
        price_html, chart_path, price_insight, daily_insight
    )

    # Step 9: Send email
    send_daily_email(
        news_china, news_nigeria, news_global,
        news_html, price_html, price_insight,
        daily_insight, chart_path, date, pdf_path
    )

    # Step 10: Export daily report for GitHub Pages
    price_insight_html = price_insight if isinstance(price_insight, str) else str(price_insight)

    save_daily_json(
        date_str=date,
        news_html=news_html,
        news_china_html=news_china,
        news_nigeria_html=news_nigeria,
        news_global_html=news_global,
        price_html=price_html,
        price_insight_html=price_insight_html,
        daily_insight_html=daily_insight,
        chart_rel_path=chart_rel_for_docs,
    )
    update_index_json(date)

    # Step 11: Git push
    logger.info("Daily report exported for GitHub Pages.")
    git_push()

    logger.info("=== Daily Solar Briefing finished ===")

if __name__ == "__main__":
    run()