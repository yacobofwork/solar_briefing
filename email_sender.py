import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils import setup_logger

logger = setup_logger("email_sender")


def build_email_html(results, price_list=None, price_insight=None):
    """构建 HTML 邮件内容（包含价格趋势 + 价格影响分析 + 分类新闻）"""

    html = """
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h1 style="color:#2A4E8A;">China PV & BESS Supply Chain Daily Briefing</h1>
    """

    # === 供应链价格影响分析 ===
    if price_insight:
        html += f"""
        <h2 style="color:#1A73E8;">📌 Price Impact Analysis</h2>
        <div style="line-height:1.6; margin-bottom:20px;">
            {price_insight}
        </div>
        """

    # === 供应链价格趋势 ===
    if price_list:
        html += """
        <h2 style="color:#1A73E8;">📊 Supply Chain Price Trends</h2>
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">
            <tr><th>Item</th><th>Price</th><th>Change</th><th>Source</th></tr>
        """
        for p in price_list:
            html += f"""
            <tr>
                <td>{p['item']}</td>
                <td>{p['price']}</td>
                <td>{p['change']}</td>
                <td>{p['source']}</td>
            </tr>
            """
        html += "</table><br>"

    # === 新闻按分类展示 ===
    html += "<h2 style='color:#1A73E8;'>📰 Industry News</h2>"

    # 按 category 分组
    grouped = {}
    for item in results:
        grouped.setdefault(item["category"], []).append(item)

    for category, items in grouped.items():
        html += f"<h3 style='color:#2A4E8A; margin-top:25px;'>{category}</h3>"

        for item in items:
            html += f"""
            <div style="border:1px solid #ddd; padding:12px; border-radius:6px; margin-bottom:12px;">
                <b>{item['title']}</b><br>
                <a href="{item['link']}" style="color:#1A73E8;">Original Link</a ><br><br>

                <div style="line-height:1.6;">
                    {item['insight']}
                </div>
            </div>
            """

    html += "</div>"
    return html



def send_with_smtp(host, port, user, password, recipients, msg):
    """内部函数：尝试使用某个 SMTP 发送"""
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



def send_email(results, price_list=None, price_insight=None,pdf_path=None):
    """支持主备邮箱自动切换的邮件发送"""

    # === 主邮箱配置 ===
    primary = {
        "host": os.getenv("PRIMARY_EMAIL_HOST"),
        "port": int(os.getenv("PRIMARY_EMAIL_PORT", 465)),
        "user": os.getenv("PRIMARY_EMAIL_USER"),
        "password": os.getenv("PRIMARY_EMAIL_PASS")
    }

    # === 备用邮箱配置 ===
    backup = {
        "host": os.getenv("BACKUP_EMAIL_HOST"),
        "port": int(os.getenv("BACKUP_EMAIL_PORT", 465)),
        "user": os.getenv("BACKUP_EMAIL_USER"),
        "password": os.getenv("BACKUP_EMAIL_PASS")
    }

    recipients = os.getenv("RECEIVERS", "").split(",")

    if not recipients:
        logger.error("未配置收件人 RECEIVERS")
        return

    # === 构建邮件 ===
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "China PV & BESS Supply Chain Daily Briefing"
    msg["From"] = primary["user"]
    msg["To"] = ", ".join(recipients)

    html_content = build_email_html(results, price_list, price_insight)
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    # 添加pdf附件
    if pdf_path:
        with open(pdf_path, "rb") as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(pdf_path))
        part["Content-Disposition"] = f'attachment; filename="{os.path.basename(pdf_path)}"'
        msg.attach(part)

    # === 1) 尝试主邮箱发送 ===
    logger.info("优先使用主邮箱发送…")
    if send_with_smtp(primary["host"], primary["port"], primary["user"], primary["password"], recipients, msg):
        return True

    # === 2) 主邮箱失败 → 自动切换备用邮箱 ===
    logger.warning("主邮箱发送失败，切换备用邮箱…")
    if send_with_smtp(backup["host"], backup["port"], backup["user"], backup["password"], recipients, msg):
        return True

    return False