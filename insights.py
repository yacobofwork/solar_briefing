import time
import os
import inspect
import json
from openai import OpenAI
from utils import clean_html, get_env

# DeepSeek API client
client = OpenAI(
    api_key=get_env("DEEPSEEK_API_KEY", required=True),
    base_url="https://api.deepseek.com",
    timeout=30
)


def safe_request(prompt):
    """
    DeepSeek API 自动重试封装
    """
    for _ in range(3):
        try:
            return client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
        except Exception:
            time.sleep(2)
    raise RuntimeError("DeepSeek API failed after 3 retries")


def load_prompt(name):
    """
    从 prompts/ 目录加载 prompt 文件
    """
    current_file = inspect.getfile(inspect.currentframe())
    base_dir = os.path.dirname(os.path.abspath(current_file))
    prompt_path = os.path.join(base_dir, "prompts", f"{name}.txt")

    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


# ============================================================
# 1) 新闻总结（结构化 JSON）
# ============================================================
def summarize_article(article):
    """
    输入: {"summary": "..."}
    输出: JSON dict（由 renderer 转成 HTML）
    """

    # ❗ 不再使用 .format()，避免破坏 JSON
    prompt = load_prompt("summarize_article")
    prompt = prompt.replace("{summary}", article["summary"])

    resp = safe_request(prompt)
    raw = resp.choices[0].message.content

    try:
        return json.loads(raw)
    except Exception:
        return {
            "title": "News Summary",
            "cn_summary": article["summary"],
            "en_summary": article["summary"],
            "cn_insights": [],
            "en_insights": [],
            "supply_chain": "",
            "nigeria_impact": "",
            "recommendation": ""
        }


# ============================================================
# 2) 价格影响分析（结构化 JSON）
# ============================================================
def analyze_price_impact(price_list):
    """
    输入: price_list
    输出: JSON dict（由 renderer 转成 HTML）
    """

    # ❗ 不再使用 .format()
    prompt = load_prompt("analyze_price_impact")
    prompt = prompt.replace("{price_list}", json.dumps(price_list, ensure_ascii=False))

    resp = safe_request(prompt)
    raw = resp.choices[0].message.content

    try:
        return json.loads(raw)
    except Exception:
        return {
            "title": "Price Impact Analysis",
            "sections": [
                {
                    "subtitle": "Error",
                    "content": "AI output could not be parsed."
                }
            ]
        }


# ============================================================
# 3) Daily Insight（结构化 JSON）
# ============================================================
def generate_daily_insight():
    """
    输出: JSON dict（由 renderer 转成 HTML）
    """
    prompt = load_prompt("daily_insight")

    resp = safe_request(prompt)
    raw = resp.choices[0].message.content

    try:
        return json.loads(raw)
    except Exception:
        return {
            "title": "Daily Insight",
            "points": [
                "AI output could not be parsed."
            ]
        }