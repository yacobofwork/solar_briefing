import os
from datetime import datetime

def build_email_html(price_insight, price_html, news_html, chart_path):
    """从模板文件加载 HTML，并替换变量"""

    template_path = os.path.join("templates", "email_template.html")

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    today = datetime.now().strftime("%Y-%m-%d")

    html = (
        template
        .replace("{{DATE}}", today)
        .replace("{{PRICE_IMPACT}}", price_insight)
        .replace("{{PRICE_TABLE}}", price_html)
        .replace("{{NEWS_SECTION}}", news_html)
        .replace("{{CHART_PATH}}", chart_path or "")
    )

    return html