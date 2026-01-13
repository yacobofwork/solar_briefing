# ingestion/region_classifier.py

import re

from solar_intel_v2.modules.insights_core import summarize_article, load_prompt

# ------------------------------------------------------------
# 可配置关键词（你可以随时扩展）
# ------------------------------------------------------------

CHINA_KEYWORDS = [
    "中国", "大陆", "内地", "光伏", "硅料", "硅片", "组件", "逆变器",
    "宁德时代", "隆基", "通威", "晶澳", "天合", "阳光电源",
    "上海", "北京", "深圳", "广州", "江苏", "浙江"
]

NIGERIA_KEYWORDS = [
    "尼日利亚", "Nigeria", "Lagos", "Abuja", "Kaduna", "Kano",
    "NERC", "TCN", "DisCo", "GenCo"
]

CHINA_DOMAINS = [
    "mp.weixin.qq.com",
    "finance.sina.com.cn",
    "cailianpress.com",
    "36kr.com",
    "jiemian.com",
    "caixin.com",
]

NIGERIA_DOMAINS = [
    "nairametrics.com",
    "businessday.ng",
    "guardian.ng",
    "punchng.com",
]

# ------------------------------------------------------------
# Region 分类主函数
# ------------------------------------------------------------

def classify_region(title: str, summary: str, link: str) -> str:
    """
    根据标题 / 摘要 / 链接域名进行自动 region 分类。
    返回：china / nigeria / global
    """

    text = f"{title} {summary}".lower()

    # 1. 域名判断（最强信号）
    for domain in CHINA_DOMAINS:
        if domain in link.lower():
            return "china"

    for domain in NIGERIA_DOMAINS:
        if domain in link.lower():
            return "nigeria"

    # 2. 关键词判断（标题 + 摘要）
    for kw in CHINA_KEYWORDS:
        if kw.lower() in text:
            return "china"

    for kw in NIGERIA_KEYWORDS:
        if kw.lower() in text:
            return "nigeria"

    # 3. 中文内容 → 默认中国
    if re.search(r"[\u4e00-\u9fff]", text):
        return "china"

    # 4. 默认 global
    return "global"



def classify_region_ai(title, summary, link, raw_text):
    base_prompt = load_prompt("region_classifier")

    final_prompt = f"""
{base_prompt}

标题：{title}
摘要：{summary}
链接：{link}
正文内容（截断）：{raw_text[:2000]}
"""

    # 你已有 summarize_article 的调用方式，这里复用
    result = summarize_article({"summary": final_prompt})
    return result