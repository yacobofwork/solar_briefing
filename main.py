from dotenv import load_dotenv
load_dotenv()

from fetcher import fetch_all_news
from insights import summarize_article
from email_sender import send_email
from utils import setup_logger, now_str

logger = setup_logger("main")


def run():
    logger.info("=== 新能源日报开始执行 ===")

    # 1) 抓取新闻
    news_list = fetch_all_news()
    if not news_list:
        logger.error("抓取失败，流程终止")
        return

    # 2) 生成洞察
    logger.info("开始生成洞察…")
    results = []
    for item in news_list:
        insight = summarize_article(item)
        results.append({
            "title": item["title"],
            "source": item["source"],
            "link": item["link"],
            "insight": insight
        })

    # 3) 发送邮件
    logger.info("开始发送邮件…")
    send_email(results)

    logger.info("=== 新能源日报执行完毕 ===")


if __name__ == "__main__":
    run()