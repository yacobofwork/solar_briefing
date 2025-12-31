import os
from openai import OpenAI
from utils import clean_html

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)


def summarize_article(article):
    prompt = f"""
你是一名新能源行业分析师，请对以下文章生成：
1. 50字摘要
2. 关键洞察（3条）
文章内容：
{article['summary']}
"""

    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return clean_html(resp.choices[0].message.content)