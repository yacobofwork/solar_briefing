import time
import os
import inspect
from openai import OpenAI
from utils import clean_html, get_env

# 该模块负责 AI
client = OpenAI(
    api_key=get_env("DEEPSEEK_API_KEY", required=True),
    base_url="https://api.deepseek.com",
    timeout=30
)

BASE_DIR = os.path.dirname(__file__)

def safe_request(prompt):
    for _ in range(3):
        try:
            return client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
        except:
            time.sleep(2)
    raise RuntimeError("DeepSeek failed")


def load_prompt(name):
    # 获取 insights.py 的真实路径（无论从哪里运行 main.py）
    current_file = inspect.getfile(inspect.currentframe())
    base_dir = os.path.dirname(os.path.abspath(current_file))

    prompt_path = os.path.join(base_dir, "prompts", f"{name}.txt")

    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def summarize_article(article):
    prompt = load_prompt("summarize_article").format(article=article["summary"])
    resp = safe_request(prompt)
    return clean_html(resp.choices[0].message.content)

def analyze_price_impact(price_list):
    prompt = load_prompt("analyze_price_impact").format(price_list=price_list)
    resp = safe_request(prompt)
    return clean_html(resp.choices[0].message.content)

def generate_daily_insight():
    prompt = load_prompt("daily_insight")
    resp = safe_request(prompt)
    return clean_html(resp.choices[0].message.content)