from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
from bs4 import BeautifulSoup


def build_pdf(**kwargs):
    """
    使用 Jinja2 渲染 PDF 模板，彻底避免 .format() 与 CSS 冲突。
    支持自动目录页、Logo、咨询公司级排版。
    """

    # 1. 加载 templates 目录
    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape(["html", "xml"])
    )

    # 2. 加载 pdf_template.html
    template = env.get_template("pdf_template.html")

    # 3. 渲染 HTML
    html_content = template.render(**kwargs)
    headings = extract_headings(html_content)
    html_content = template.render(**kwargs,headings=headings)

    # 4. 生成 PDF
    (HTML(string=html_content,
         base_url=".") # WeasyPrint 会使用base_url作为根目录
     .write_pdf(kwargs["output_path"]))


# 标题扫描器
def extract_headings(html):
    soup = BeautifulSoup(html, "html.parser")
    headings = []
    for tag in soup.find_all(["h1", "h2"]):
        if tag.get("id"):
            headings.append({
                "id": tag["id"],
                "text": tag.get_text(strip=True)
            })
    return headings