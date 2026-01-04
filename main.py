from dotenv import load_dotenv
load_dotenv()

import os
import shutil
import datetime

from chart_builder import build_price_chart
from fetch_prices import fetch_all_prices
from fetcher import fetch_all_news

from insights import (
    summarize_article,
    analyze_price_impact,
    generate_daily_insight
)

from renderers.article_renderer import render_article
from renderers.price_renderer import render_price_insight
from renderers.insight_renderer import render_daily_insight

from pdf_builder import build_pdf
from email_sender import send_email
from utils import setup_logger
from cache_manager import DailyCache
import yaml

# ⭐ 新增：引入外部 URL → 原始 news 的管道
from ingestion.external_news_pipeline import process_pending_urls_to_raw_news

logger = setup_logger("main")

history_file = "price_history.csv"

# 初始化天缓存，可在配置文件当中关闭
config = yaml.safe_load(open("config.yaml", encoding="utf-8"))
cache_enabled = config["cache"]["enabled"]
cache = DailyCache(config["cache"]["path"])

# 自动清理缓存
keep_days = config["cache"]["keep_days"]
cache.clean_old_cache(keep_days)


# ============================================================
# 1. 数据抓取层
# ============================================================

def fetch_data():
    """抓取价格与新闻（带缓存），并接入外部 URL 管道。"""
    # ---- Price Cache ----
    if cache_enabled and cache.exists("prices"):
        logger.info("Loading prices from cache...")
        price_list = cache.load("prices")
    else:
        logger.info("Fetching price data...")
        price_list = fetch_all_prices()
        if cache_enabled:
            cache.save("prices", price_list)

    # ---- News Cache ----
    if cache_enabled and cache.exists("news_raw"):
        logger.info("Loading raw news from cache...")
        news_list = cache.load("news_raw")
    else:
        logger.info("Fetching news data...")
        news_list = fetch_all_news()
        if cache_enabled:
            cache.save("news_raw", news_list)

    # ---- External URLs → 原始新闻 ----
    logger.info("Processing external URL queue for additional news...")
    external_news = process_pending_urls_to_raw_news()
    if external_news:
        logger.info(f"Added {len(external_news)} external news items.")
        news_list.extend(external_news)
        # 如果你希望 external 也参与 news_raw 缓存，下次命中缓存时也能看到：
        if cache_enabled:
            cache.save("news_raw", news_list)
    else:
        logger.info("No external news items added.")

    return price_list, news_list


# ============================================================
# 2. AI 处理层
# ============================================================

def process_news_ai(news_list):
    """AI 处理新闻（带缓存）"""
    if cache_enabled and cache.exists("news_ai"):
        logger.info("Loading AI-processed news from cache...")
        return cache.load("news_ai")

    logger.info("Processing news with AI...")
    results = []
    for item in news_list:
        article_obj = {
            "summary": item.get("summary", item["title"]),
            "source": item.get("source", "Unknown"),
            "link": item.get("link", None),
            "pub_date": item.get("pub_date", None)
        }
        ai_json = summarize_article(article_obj)
        results.append(ai_json)

    if cache_enabled:
        cache.save("news_ai", results)

    return results


def process_price_ai(price_list, date):
    """价格历史记录、图表生成、价格洞察（带缓存）"""
    # ---- Price Insight Cache ----
    if cache_enabled and cache.exists("price_insight"):
        logger.info("Loading price insight from cache...")
        price_insight = cache.load("price_insight")
    else:
        raw_price_insight = analyze_price_impact(price_list)
        price_insight = render_price_insight(raw_price_insight)
        if cache_enabled:
            cache.save("price_insight", price_insight)

    # ---- Chart Cache ----
    charts_dir = "output/charts"
    os.makedirs(charts_dir, exist_ok=True)
    chart_path = os.path.abspath(f"{charts_dir}/price_chart_{date}.png")
    if cache_enabled and os.path.exists(chart_path):
        logger.info("Using cached chart...")
    else:
        logger.info("Generating price chart...")
        build_price_chart(history_file, chart_path)

    return chart_path, price_insight


# ============================================================
# 3. 数据分组层（Region）
# ============================================================

def group_news_by_region(results):
    """按 region 分组（带缓存）"""
    if cache_enabled and cache.exists("china"):
        logger.info("Loading region groups from cache...")
        return (
            cache.load("china"),
            cache.load("nigeria"),
            cache.load("global")
        )

    china = [r for r in results if r.get("region") == "china"]
    nigeria = [r for r in results if r.get("region") == "nigeria"]
    global_news = [r for r in results if r.get("region") == "global"]

    if cache_enabled:
        cache.save("china", china)
        cache.save("nigeria", nigeria)
        cache.save("global", global_news)

    return china, nigeria, global_news


# ============================================================
# 4. 渲染层（HTML）
# ============================================================

def render_news_sections(china, nigeria, global_news):
    """渲染邮件用的 news_html（带标题）"""
    html = ""

    if china:
        html += "<h2> 🇨🇳China Supply Chain</h2>"
        for item in china:
            html += render_article(item)

    if nigeria:
        html += "<h2>🇳🇬Nigeria Market</h2>"
        for item in nigeria:
            html += render_article(item)

    if global_news:
        html += "<h2> 🌍Global Solar & Storage</h2>"
        for item in global_news:
            html += render_article(item)

    return html


def render_pdf_sections(china, nigeria, global_news):
    """渲染 PDF 用的三个分区（不带标题，由模板控制）"""
    news_china = "".join(render_article(n) for n in china)
    news_nigeria = "".join(render_article(n) for n in nigeria)
    news_global = "".join(render_article(n) for n in global_news)
    return news_china, news_nigeria, news_global


def render_price_table(price_list):
    """渲染价格表 HTML"""
    if not price_list:
        return "<p>No price data available today.</p >"

    html = """
    <table>
        <tr><th>Item</th><th>Price</th><th>Change</th><th>Source</th></tr>
    """
    for p in price_list:
        html += f"""
        <tr>
            <td>{p['item']}</td>
            <td>{p['price']}</td>
            <td>{p['change']}</td>
            <td>{p['source']}</td>
        </tr>
        """
    html += "</table>"
    return html


# ============================================================
# 5. 输出层（PDF + 邮件）
# ============================================================

def export_pdf(date, news_html, news_china, news_nigeria, news_global,
               price_html, chart_path, price_insight, daily_insight):

    pdf_dir = "output/pdf"
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.abspath(f"{pdf_dir}/daily_report_{date}.pdf")

    logo_path = os.path.abspath("company_logo.png")

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

    logger.info(f"PDF 已生成：{pdf_path}")

    # 归档
    archive_dir = "output/archive"
    os.makedirs(archive_dir, exist_ok=True)
    shutil.copy(pdf_path, os.path.join(archive_dir, f"daily_report_{date}.pdf"))

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
        logger.info("邮件发送成功")
    else:
        logger.error("邮件发送失败")


def safe_delete(path):
    try:
        if os.path.exists(path):
            os.remove(path)
            return True
    except Exception as e:
        print(f"Failed to delete {path}: {e}")
    return False


# ============================================================
# 主流程（Pipeline）
# ============================================================

def run():
    logger.info("=== 新能源日报开始执行 ===")

    # Step 1: 抓取数据（含外部 URL 注入）
    price_list, news_list = fetch_data()

    # Step 2: AI 处理新闻
    ai_results = process_news_ai(news_list)

    # Step 3: Region 分组
    china_news, nigeria_news, global_news = group_news_by_region(ai_results)

    # Step 4: 日期
    date = datetime.date.today().strftime("%Y-%m-%d")

    # Step 5: 价格处理
    chart_path, price_insight = process_price_ai(price_list, date)

    # Step 6: 渲染 HTML
    news_html = render_news_sections(china_news, nigeria_news, global_news)
    news_china, news_nigeria, news_global = render_pdf_sections(
        china_news, nigeria_news, global_news
    )
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

    # Step 8: PDF 输出
    pdf_path = export_pdf(
        date, news_html, news_china, news_nigeria, news_global,
        price_html, chart_path, price_insight, daily_insight
    )

    # Step 9: 邮件发送
    send_daily_email(
        news_china, news_nigeria, news_global,
        news_html, price_html, price_insight,
        daily_insight, chart_path, date, pdf_path
    )


if __name__ == "__main__":
    run()