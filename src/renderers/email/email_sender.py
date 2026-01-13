import os
import smtplib
from pathlib import Path
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.system.config_loader import load_config
from src.system.logger import setup_logger
from src.system.utils import get_env

config = load_config()

logger = setup_logger("email_sender")


# ============================
# Render HTML template with Jinja2
# ============================
def render_email_html(**kwargs) -> str:
    templates_dir = Path(config["paths"]["templates_dir"]).resolve()
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html", "xml"])
    )
    try:
        template = env.get_template("email_template.html")
        return template.render(**kwargs)
    except Exception as e:
        logger.error(f"Failed to render email template: {e}")
        return "<p>Email template error.</p >"


# ============================
# Internal function: try sending with SMTP
# ============================
def send_with_smtp(host, port, user, password, recipients, msg) -> bool:
    try:
        logger.info(f"Trying SMTP send: {host}:{port}, user={user}")
        server = smtplib.SMTP_SSL(host, port)
        server.login(user, password)
        server.sendmail(user, recipients, msg.as_string())
        server.quit()
        logger.info("Email sent successfully via SMTP.")
        return True
    except Exception as e:
        logger.error(f"SMTP send failed: {e}")
        return False


# ============================
# Main function: support primary/backup email
# ============================
def send_email(
    news_china,
    news_nigeria,
    news_global,
    news_html,
    price_html,
    price_insight,
    daily_insight,
    chart_path,
    date,
    pdf_path=None
) -> bool:
    """Send daily report email (supports primary/backup SMTP, HTML template, chart embed, PDF attachment)."""

    # Primary email config
    primary = {
        "host": get_env("PRIMARY_EMAIL_HOST"),
        "port": int(get_env("PRIMARY_EMAIL_PORT", default=465)),
        "user": get_env("PRIMARY_EMAIL_USER"),
        "password": get_env("PRIMARY_EMAIL_PASS"),
    }

    # Backup email config
    backup = {
        "host": get_env("BACKUP_EMAIL_HOST"),
        "port": int(get_env("BACKUP_EMAIL_PORT", default=465)),
        "user": get_env("BACKUP_EMAIL_USER"),
        "password": get_env("BACKUP_EMAIL_PASS"),
    }

    # Recipients: YAML first，.env second
    recipients = config.get("email", {}).get("receivers", [])
    if not recipients:
        recipients_env = get_env("RECEIVERS", "")
        recipients = [r.strip() for r in recipients_env.split(",") if r.strip()]
    if not recipients:
        logger.error("No recipients configured (email.receivers or RECEIVERS).")
        return False

    # Render HTML
    html_content = render_email_html(
        news_china=news_china,
        news_nigeria=news_nigeria,
        news_global=news_global,
        date=date,
        price_insight=price_insight,
        price_html=price_html,
        news_html=news_html,
        daily_insight=daily_insight
    )

    # Build email
    msg = MIMEMultipart("related")
    msg["Subject"] = f"Daily Solar & Storage Intelligence - {date}"
    msg["From"] = primary["user"]
    msg["To"] = ", ".join(recipients)

    # HTML part
    msg_alt = MIMEMultipart("alternative")
    msg.attach(msg_alt)
    msg_alt.attach(MIMEText(html_content, "html", "utf-8"))

    # Chart embed
    if chart_path and os.path.exists(chart_path):
        try:
            with open(chart_path, "rb") as f:
                img = MIMEImage(f.read())
            img.add_header("Content-ID", "<price_chart>")
            img.add_header("Content-Disposition", "inline", filename=os.path.basename(chart_path))
            msg.attach(img)
        except Exception as e:
            logger.warning(f"Failed to embed chart: {e}")
    else:
        logger.warning("Chart file not found, skipping embed.")

    # PDF attachment
    if pdf_path and os.path.exists(pdf_path):
        try:
            with open(pdf_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(pdf_path))
            part["Content-Disposition"] = f'attachment; filename="{os.path.basename(pdf_path)}"'
            msg.attach(part)
        except Exception as e:
            logger.warning(f"Failed to attach PDF: {e}")
    else:
        logger.warning("PDF file not found, skipping attachment.")

    # Try primary SMTP
    logger.info("Attempting to send via primary SMTP...")
    if send_with_smtp(primary["host"], primary["port"], primary["user"], primary["password"], recipients, msg):
        return True

    # Fallback to backup SMTP
    logger.warning("Primary SMTP failed, switching to backup SMTP...")
    if send_with_smtp(backup["host"], backup["port"], backup["user"], backup["password"], recipients, msg):
        return True

    logger.error("Both primary and backup SMTP failed.")
    return False