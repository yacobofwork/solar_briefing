from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
from bs4 import BeautifulSoup

from src.system.config_loader import load_config
from src.system.logger import setup_logger

config = load_config()

logger = setup_logger("pdf_builder")

def build_pdf(**kwargs):
    """
    Render PDF using Jinja2 + WeasyPrint.
    Supports automatic table of contents, logo, and professional layout.
    """
    try:
        # 1. Load templates directory
        templates_dir = Path(config["paths"]["templates_dir"]).resolve()
        if not templates_dir.exists():
            logger.error(f"Templates directory not found: {templates_dir}")
            return None

        env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(["html", "xml"])
        )

        # 2. Load pdf_template.html
        template = env.get_template("pdf_template.html")

        # 3. Render HTML with headings
        html_content = template.render(**kwargs)
        headings = extract_headings(html_content)
        html_content = template.render(**kwargs, headings=headings)

        # 4. Generate PDF
        output_path = kwargs.get("output_path")
        if not output_path:
            logger.error("Missing output_path in build_pdf kwargs.")
            return None

        HTML(string=html_content, base_url=str(templates_dir)).write_pdf(output_path)
        logger.info(f"PDF generated successfully: {output_path}")
        return str(output_path)

    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        return None



def extract_headings(html: str):
    """
    Extract headings (h1, h2) with IDs for table of contents.
    """
    soup = BeautifulSoup(html, "html.parser")
    headings = []
    for tag in soup.find_all(["h1", "h2"]):
        if tag.get("id"):
            headings.append({
                "id": tag["id"],
                "text": tag.get_text(strip=True)
            })
    return headings