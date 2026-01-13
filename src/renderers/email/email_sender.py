import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

from jinja2 import Environment, FileSystemLoader, select_autoescape
from solar_intel_v2.system.utils import setup_logger, get_env

logger = setup_logger("email_sender")


# ============================
# 使用 Jinja2 渲染 HTML 模板
# ============================
def render_email_html(**kwargs):
    env = Environment(
        loader=FileSystemLoader("../../../templates"),
        autoescape=select_autoescape(["html", "xml"])
    )
    template = env.get_template("email_template.html")
    return template.render(**kwargs)


# ============================
# 内部函数：尝试使用某个 SMTP 发送
# ============================
def send_with_smtp(host, port, user, password, recipients, msg):
    try:
        logger.info(f"尝试 SMTP 发送：{host}:{port} 用户={user}")
        server = smtplib.SMTP_SSL(host, port)
        server.login(user, password)
        server.sendmail(user, recipients, msg.as_string())
        server.quit()
        logger.info("发送成功")
        return True
    except Exception as e:
        logger.error(f"发送失败：{e}")
        return False


# ============================
# 主函数：支持主备邮箱自动切换
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
):
    """发送日报邮件（支持主备邮箱自动切换 + HTML 模板 + 图表嵌入 + PDF 附件）"""

    # === 主邮箱配置 ===
    primary = {
        "host": get_env("PRIMARY_EMAIL_HOST"),
        "port": int(get_env("PRIMARY_EMAIL_PORT", default=465)),
        "user": get_env("PRIMARY_EMAIL_USER"),
        "password": get_env("PRIMARY_EMAIL_PASS"),
    }

    # === 备用邮箱配置 ===
    backup = {
        "host": get_env("BACKUP_EMAIL_HOST"),
        "port": int(get_env("BACKUP_EMAIL_PORT", default=465)),
        "user": get_env("BACKUP_EMAIL_USER"),
        "password": get_env("BACKUP_EMAIL_PASS"),
    }

    # === 收件人 ===
    recipients = get_env("RECEIVERS", "").split(",")
    if not recipients:
        logger.error("未配置收件人 RECEIVERS")
        return False

    # === 使用 Jinja2 渲染 HTML ===
    html_content = render_email_html(
        news_china = news_china,
        news_nigeria = news_nigeria,
        news_global = news_global,
        date=date,
        price_insight=price_insight,
        price_html=price_html,
        news_html=news_html,
        daily_insight=daily_insight
    )

    # === 构建邮件 ===
    msg = MIMEMultipart("related")
    msg["Subject"] = f"Daily Solar & Storage Intelligence - {date}"
    msg["From"] = primary["user"]
    msg["To"] = ", ".join(recipients)

    # HTML 部分
    msg_alt = MIMEMultipart("alternative")
    msg.attach(msg_alt)
    msg_alt.attach(MIMEText(html_content, "html", "utf-8"))

    # === 图表嵌入（cid:price_chart） ===
    if chart_path and os.path.exists(chart_path):
        with open(chart_path, "rb") as f:
            img = MIMEImage(f.read())
            img.add_header("Content-ID", "<price_chart>")
            img.add_header("Content-Disposition", "inline", filename=os.path.basename(chart_path))
            msg.attach(img)
    else:
        logger.warning("图表文件不存在，跳过嵌入图表")

    # === PDF 附件 ===
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(pdf_path))
        part["Content-Disposition"] = f'attachment; filename="{os.path.basename(pdf_path)}"'
        msg.attach(part)
    else:
        logger.warning("PDF 文件不存在，跳过附件")

    # === 1) 尝试主邮箱发送 ===
    logger.info("优先使用主邮箱发送…")
    if send_with_smtp(primary["host"], primary["port"], primary["user"], primary["password"], recipients, msg):
        return True

    # === 2) 主邮箱失败 → 自动切换备用邮箱 ===
    logger.warning("主邮箱发送失败，切换备用邮箱…")
    if send_with_smtp(backup["host"], backup["port"], backup["user"], backup["password"], recipients, msg):
        return True

    logger.error("主备邮箱均发送失败")
    return False