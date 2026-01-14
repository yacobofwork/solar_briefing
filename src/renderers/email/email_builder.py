from pathlib import Path
from datetime import datetime
from src.system.logger import setup_logger

logger = setup_logger("main")


def build_email_html(price_insight: str, price_html: str, news_html: str, chart_path: str) -> str:
    """
    Build email HTML from template and replace placeholders.
    Template is located in src/renderers/templates/email_template.html
    """
    template_path = Path(__file__).resolve().parent / "templates" / "email_template.html"

    if not template_path.exists():
        logger.error(f"Email template not found: {template_path}")
        return "<p>Email template missing.</p >"

    try:
        template = template_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to read email template: {e}")
        return "<p>Email template error.</p >"

    today = datetime.now().strftime("%Y-%m-%d")

    replacements = {
        "{{DATE}}": today,
        "{{PRICE_IMPACT}}": price_insight or "",
        "{{PRICE_TABLE}}": price_html or "",
        "{{NEWS_SECTION}}": news_html or "",
        "{{CHART_PATH}}": chart_path or "",
    }

    for key, value in replacements.items():
        template = template.replace(key, value)

    logger.info("Email HTML built successfully.")
    return template