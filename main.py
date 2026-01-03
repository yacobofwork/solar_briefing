from dotenv import load_dotenv
load_dotenv()

import os
import shutil
import csv
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

logger = setup_logger("main")

history_file = "price_history.csv"


# ============================================================
# 1. 数据抓取层
# ============================================================

def fetch_data():
    """抓取价格与新闻"""
    logger.info("Fetching price data...")
    price_list = fetch_all_prices()

    logger.info("Fetching news data...")
    news_list = fetch_all_news()

    return price_list, news_list


# ============================================================
# 2. AI 处理层
# ============================================================

def process_news_ai(news_list):
    """对每条新闻调用 summarize_article()，生成结构化 JSON"""
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

    return results


def process_price_ai(price_list, date):
    """价格历史记录、图表生成、价格洞察"""
    if not price_list:
        return None, "<p>No price data available today.</p >"

    file_exists = os.path.exists(history_file)

    # 写入历史记录
    with open(history_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["date", "item", "price"])
        for p in price_list:
            writer.writerow([date, p["item"], p["price"]])

    # 图表
    chart_path = f"price_chart_{date}.png"
    build_price_chart(history_file, chart_path)

    # AI 价格洞察
    raw_price_insight = analyze_price_impact(price_list)
    price_insight = render_price_insight(raw_price_insight)

    return chart_path, price_insight


# ============================================================
# 3. 数据分组层（Region）
# ============================================================

def group_news_by_region(results):
    """按 region 分组：china / nigeria / global"""
    china = [r for r in results if r.get("region") == "china"]
    nigeria = [r for r in results if r.get("region") == "nigeria"]
    global_news = [r for r in results if r.get("region") == "global"]

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

    pdf_path = f"daily_report_{date}.pdf"

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
        logo_path=os.path.abspath("company_logo.png"),
        output_path=pdf_path
    )

    logger.info(f"PDF 已生成：{pdf_path}")

    # 归档
    archive_dir = "archive_pdf"
    os.makedirs(archive_dir, exist_ok=True)
    shutil.copy(pdf_path, os.path.join(archive_dir, f"daily_report_{date}.pdf"))

    return pdf_path


def send_daily_email(news_html, price_html, price_insight,
                     daily_insight,chart_path, date, pdf_path):

    ok = send_email(
        news_html=news_html,
        price_html=price_html,
        price_insight=price_insight,
        daily_insight=daily_insight,
        chart_path=chart_path,
        date=date,
        pdf_path=pdf_path
    )

    if ok:
        logger.info("邮件发送成功")
    else:
        logger.error("邮件发送失败")


# ============================================================
# 主流程（Pipeline）
# ============================================================

def run():
    logger.info("=== 新能源日报开始执行 ===")

    # Step 1: 抓取数据
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
    raw_daily_insight = generate_daily_insight()
    daily_insight = render_daily_insight(raw_daily_insight)

    # Step 8: PDF 输出
    pdf_path = export_pdf(
        date, news_html, news_china, news_nigeria, news_global,
        price_html, chart_path, price_insight, daily_insight
    )

    # Step 9: 邮件发送
    send_daily_email(
        news_html, price_html, price_insight, daily_insight,
        chart_path, date, pdf_path
    )


if __name__ == "__main__":
    run()