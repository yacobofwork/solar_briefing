from dotenv import load_dotenv
load_dotenv()

import os
import shutil
import csv
import datetime

from chart_builder import build_price_chart
from fetch_prices import fetch_all_prices
from fetcher import fetch_all_news
from insights import summarize_article, classify_article, analyze_price_impact
from pdf_builder import build_pdf
from email_sender import send_email
from utils import setup_logger

logger = setup_logger("main")

history_file = "price_history.csv"


def run():
    logger.info("=== 新能源日报开始执行 ===")
    file_exists = os.path.exists(history_file)

    # ============================
    # 1) 抓取供应链价格
    # ============================
    price_list = fetch_all_prices()

    # ============================
    # 2) 抓取新闻
    # ============================
    news_list = fetch_all_news()

    # ============================
    # 3) 分类 + 洞察
    # ============================
    results = []
    for item in news_list:
        article_obj = {
            "summary": item.get("summary", item["title"])
        }

        summary = summarize_article(article_obj)
        category = classify_article(article_obj)

        results.append({
            "title": item["title"],
            "link": item["link"],
            "category": category,
            "insight": summary
        })

    # ============================
    # 4) 日期
    # ============================
    date = datetime.date.today().strftime("%Y-%m-%d")

    # ============================
    # 5) 新闻按分类分组
    # ============================
    grouped = {}
    for r in results:
        grouped.setdefault(r["category"], []).append(r)

    # ============================
    # 6) 价格相关流程
    # ============================
    if price_list:
        # 写入历史价格
        with open(history_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["date", "item", "price"])
            for p in price_list:
                writer.writerow([date, p["item"], p["price"]])

        # 生成图表
        chart_path = f"price_chart_{date}.png"
        build_price_chart("price_history.csv", chart_path)

        # 价格影响分析
        price_insight = analyze_price_impact(price_list)
    else:
        logger.warning("今日未获取到价格数据，跳过价格相关流程")
        chart_path = None
        price_insight = "No price data available today."

    # ============================
    # 7) 构建 PDF 所需 HTML 片段
    # ============================

    # ---- 价格表格 HTML ----
    if price_list:
        price_html = """
        <table>
            <tr><th>Item</th><th>Price</th><th>Change</th><th>Source</th></tr>
        """
        for p in price_list:
            price_html += f"""
            <tr>
                <td>{p['item']}</td>
                <td>{p['price']}</td>
                <td>{p['change']}</td>
                <td>{p['source']}</td>
            </tr>
            """
        price_html += "</table>"
    else:
        price_html = "<p>No price data available today.</p >"

    # ---- 新闻 HTML ----
    news_html = ""
    for category, items in grouped.items():
        news_html += f"<h2>{category}</h2>"
        for item in items:
            news_html += f"""
            <div class="news-item">
                <div class="news-title">{item['title']}</div>
                <div class="news-summary">{item['insight']}</div>
                <a class="news-link" href=" 'link']">Original link</a >
            </div>
            """

    # ============================
    # 8) 生成 PDF
    # ============================
    pdf_path = f"daily_report_{date}.pdf"

    build_pdf(
        news_html=news_html,
        price_html=price_html,
        chart_path=chart_path,
        date=date,
        price_insight=price_insight,
        output_path=pdf_path
    )

    logger.info(f"PDF 已生成：{pdf_path}")

    # 保存 HTML（可选）
    with open("daily_report.html", "w", encoding="utf-8") as f:
        f.write(news_html + price_html)

    # 归档 PDF
    archive_dir = "archive_pdf"
    os.makedirs(archive_dir, exist_ok=True)
    archive_path = os.path.join(archive_dir, f"daily_report_{date}.pdf")
    shutil.copy(pdf_path, archive_path)
    logger.info(f"PDF 已归档：{archive_path}")

    # ============================
    # 9) 发送邮件
    # ============================
    ok = send_email(
        news_html=news_html,
        price_html=price_html,
        price_insight=price_insight,
        daily_insight="",
        chart_path=chart_path,
        date=date,
        pdf_path=pdf_path
    )

    if ok:
        logger.info("邮件发送成功")
    else:
        logger.error("邮件发送失败")


if __name__ == "__main__":
    run()