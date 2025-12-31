import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils import setup_logger
import os

logger = setup_logger("email")


def build_email_html(results):
    html = "<h2>新能源日报</h2><br>"

    for item in results:
        html += f"""
        <div style="margin-bottom:20px;">
            <b>{item['title']}</b><br>
            <i>{item['source']}</i><br>
            <a href=" 'link']">原文链接</a ><br>
            <p>{item['insight']}</p >
        </div>
        <hr>
        """

    return html


def send_with_smtp(host, port, user, password, receivers, subject, content):
    """通用 SMTP 发送函数（支持 SSL / TLS）"""

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = ", ".join(receivers)
    msg.attach(MIMEText(content, "html", "utf-8"))

    port = int(port)

    try:
        if port == 465:
            # SSL
            server = smtplib.SMTP_SSL(host, port)
        else:
            # TLS
            server = smtplib.SMTP(host, port)
            server.starttls()

        server.login(user, password)
        server.sendmail(user, receivers, msg.as_string())
        server.quit()

        return True

    except Exception as e:
        logger.error(f"SMTP 发送失败: {e}")
        return False


def send_email(results):
    """主入口：主邮箱优先，失败自动切换备用邮箱"""

    subject = "新能源日报"
    content = build_email_html(results)
    receivers = os.getenv("RECEIVERS").split(",")

    # 主邮箱
    primary = {
        "host": os.getenv("PRIMARY_EMAIL_HOST"),
        "port": os.getenv("PRIMARY_EMAIL_PORT"),
        "user": os.getenv("PRIMARY_EMAIL_USER"),
        "pass": os.getenv("PRIMARY_EMAIL_PASS"),
    }

    # 备用邮箱
    backup = {
        "host": os.getenv("BACKUP_EMAIL_HOST"),
        "port": os.getenv("BACKUP_EMAIL_PORT"),
        "user": os.getenv("BACKUP_EMAIL_USER"),
        "pass": os.getenv("BACKUP_EMAIL_PASS"),
    }

    # 先尝试主邮箱
    logger.info("尝试使用主邮箱发送…")
    ok = send_with_smtp(
        primary["host"], primary["port"], primary["user"], primary["pass"],
        receivers, subject, content
    )

    if ok:
        logger.info("主邮箱发送成功")
        return

    # 主邮箱失败 → 自动切换备用邮箱
    logger.warning("主邮箱失败，切换备用邮箱…")

    ok = send_with_smtp(
        backup["host"], backup["port"], backup["user"], backup["pass"],
        receivers, subject, content
    )

    if ok:
        logger.info("备用邮箱发送成功")
    else:
        logger.error("备用邮箱也发送失败，邮件未送达")