
from dotenv import load_dotenv
load_dotenv()

from fetch_prices import fetch_all_prices
from fetcher import fetch_all_news
from insights import summarize_article, classify_article, analyze_price_impact
from pdf_builder import build_pdf_html
from email_sender import send_email
from utils import setup_logger
import datetime
from pdf_builder import html_to_pdf


logger = setup_logger("main")


def run():
    logger.info("=== 新能源日报开始执行 ===")

    # 1) 抓取供应链价格
    price_list = fetch_all_prices()

    # 2) 抓取新闻
    news_list = fetch_all_news()

    # 3) 分类 + 洞察
    results = []
    for item in news_list:
        # 构造 summarize_article 所需的 article 对象
        article_obj = {
            "summary": item["title"] + "\n" + item["link"]
        }

        summary = summarize_article(article_obj)
        category = classify_article(article_obj)

        results.append({
            "title": item["title"],
            "link": item["link"],
            "category": category,
            "insight": summary
        })

    # 4) 价格影响分析
    price_insight = analyze_price_impact(price_list)

    # 5) === 在这里生成 PDF ===
    date = datetime.date.today().strftime("%Y-%m-%d")

    # 按分类分组新闻
    grouped = {}
    for r in results:
        grouped.setdefault(r["category"], []).append(r)

    pdf_html = build_pdf_html(
        date=date,
        price_insight=price_insight,
        price_list=price_list,
        news_grouped=grouped
    )

    # 生成 PDF 文件
    pdf_path = f"daily_report_{date}.pdf"
    html_to_pdf(pdf_html, pdf_path)
    logger.info(f"PDF 已生成：{pdf_path}")

    # 你可以选择保存 PDF HTML（可选）
    with open("daily_report.html", "w", encoding="utf-8") as f:
        f.write(pdf_html)


    # 6) 发送邮件（仍然使用 HTML 邮件）
    send_email(results, price_list, price_insight)


if __name__ == "__main__":
    run()