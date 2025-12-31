import os
import time
from openai import OpenAI
from utils import clean_html

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    timeout=30  # 国内网络必须加长超时
)

def safe_request(prompt, retries=3):
    """DeepSeek API 自动重试封装（适合国内网络）"""
    for i in range(retries):
        try:
            return client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
        except Exception as e:
            print(f"[WARN] DeepSeek 调用失败（第 {i+1} 次）: {e}")
            time.sleep(2)

    raise RuntimeError("DeepSeek API 多次重试仍失败")

def summarize_article(article):
    prompt = f"""
You are an energy supply chain analyst specializing in China's PV and BESS industries.
Generate a bilingual intelligence brief for our UK-based team working on Nigeria microgrid projects.

【Content Requirements】
1. Chinese Summary (50 characters)
2. English Summary (50 words)
3. Chinese Key Insights (3 bullet points)
4. English Key Insights (3 bullet points)

【Supply Chain Impact – English Only】
5. Impact on PV/BESS supply chain (price, lead time, capacity, export)
6. Impact on our Nigeria microgrid projects (CAPEX, delivery, risk)
7. Procurement recommendation (actionable, concise)

【Article】
{article['summary']}
"""

    resp = safe_request(prompt)
    return clean_html(resp.choices[0].message.content)

def classify_article(article):
    """自动分类：PV / BESS / Inverter / Policy / Supply Chain"""
    prompt = f"""
You are an expert in China's PV and BESS industries.
Classify the following news into ONE category:

Categories:
1. PV (solar modules, wafers, cells, mounting, trackers)
2. BESS (battery cells, PACK, BMS, energy storage systems)
3. Inverter (PV inverter, hybrid inverter, PCS)
4. Policy (government policy, regulation, subsidy, export rule)
5. Supply Chain (price, capacity, export, logistics, risk)

Return ONLY the category name.

News:
{article['summary']}
"""

    resp = safe_request(prompt)
    return resp.choices[0].message.content.strip()