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
你是一名新能源光伏和储能行业分析师，请对以下文章生成中英双语内容：

【要求】
1. 中文摘要（50 字以内）
2. 英文摘要（50 words）
3. 中文关键洞察（3 条，每条 20 字以内）
4. 英文关键洞察（3 条，每条 20 words）

【文章内容】
{article['summary']}
"""

    resp = safe_request(prompt)
    return clean_html(resp.choices[0].message.content)