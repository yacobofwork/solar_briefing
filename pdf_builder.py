import os
from weasyprint import HTML

def load_template():
    """读取 PDF HTML 模板文件"""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "pdf_template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

def build_pdf(news_html, price_html, chart_path, date, price_insight, daily_insight, output_path):
    """构建 PDF 报告"""
    template = load_template()

    # 将变量注入 HTML 模板
    html_content = template.format(
        date=date,
        price_insight=price_insight,
        price_html=price_html,
        news_html=news_html,
        daily_insight=daily_insight,
        chart_path=chart_path
    )

    # 生成 PDF
    HTML(string=html_content).write_pdf(output_path)