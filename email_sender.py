import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils import setup_logger
import os
import re
from datetime import datetime

logger = setup_logger("email")

def extract_section(text, keyword):
    """从模型输出中提取指定段落"""
    pattern = rf"{keyword}[:：]\s*(.*?)(?=\n[A-Za-z\u4e00-\u9fa5]|$)"
    match = re.search(pattern, text, re.S)
    return match.group(1).strip() if match else text

def build_email_html(results):
    today = datetime.now().strftime("%Y-%m-%d")

    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">

        <h1 style="color: #2A4E8A; border-bottom: 2px solid #2A4E8A; padding-bottom: 10px;">
            新能源日报（中英双语版） <span style="font-size:16px; color:#666;">{today}</span>
        </h1>
    """

    grouped = {}
    for item in results:
        grouped.setdefault(item["source"], []).append(item)

    for source, items in grouped.items():
        html += f"""
        <h2 style="color:#1A73E8; margin-top:30px;">{source}</h2>
        """

        for item in items:
            html += f"""
            <div style="
                border:1px solid #ddd;
                border-radius:8px;
                padding:15px;
                margin-bottom:15px;
                background:#fafafa;
            ">
                <h3 style="margin:0; color:#333;">{item['title']}</h3>
                <p style="margin:5px 0;">
                    <a href=" 'link']" style="color:#1A73E8;">原文链接</a >
                </p >

                <div style="margin-top:10px; line-height:1.6;">

                    <b>【中文摘要】</b><br>
                    {extract_section(item['insight'], "中文摘要")}

                    <br><b>【English Summary】</b><br>
                    {extract_section(item['insight'], "英文摘要")}

                    <br><b>【中文洞察】</b><br>
                    {extract_section(item['insight'], "中文关键洞察")}

                    <br><b>【English Insights】</b><br>
                    {extract_section(item['insight'], "英文关键洞察")}
                </div>
            </div>
            """

    html += "</div>"
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