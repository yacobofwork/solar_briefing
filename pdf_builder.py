from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML


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

    # 4. 生成 PDF
    (HTML(string=html_content,
         base_url=".") # WeasyPrint 会使用base_url作为根目录
     .write_pdf(kwargs["output_path"]))