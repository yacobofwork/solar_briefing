import time
import json
from pathlib import Path

from openai import OpenAI
from src.system.utils import get_env
from src.system.logger import setup_logger

logger = setup_logger("insights_core")

# ============================================================
# DeepSeek API client
# ============================================================
client = OpenAI(
    api_key=get_env("DEEPSEEK_API_KEY", required=True),
    base_url="https://api.deepseek.com",
    timeout=30
)


def safe_request(prompt: str):
    """
    Wrapper for DeepSeek API with automatic retries.
    """
    for attempt in range(3):
        try:
            return client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
        except Exception as e:
            logger.warning(f"DeepSeek API request failed (attempt {attempt+1}): {e}")
            time.sleep(2)
    logger.error("DeepSeek API failed after 3 retries")
    raise RuntimeError("DeepSeek API failed after 3 retries")

def load_prompt(name: str) -> str:
    """
    Load prompt file from src/prompts/{name}.txt
    """
    project_root = Path(__file__).resolve().parents[1]  # 回到 src/
    prompt_path = project_root / "prompts" / f"{name}.txt"

    if not prompt_path.exists():
        logger.error(f"Prompt file not found: {prompt_path}")
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    with prompt_path.open("r", encoding="utf-8") as f:
        return f.read()


# ============================================================
# 1) News Summary (structured JSON)
# ============================================================
def summarize_article(article: dict) -> dict:
    """
    Input: {"summary": "..."}
    Output: JSON dict (rendered into HTML later)
    """
    prompt = load_prompt("summarize_article")
    prompt = prompt.replace("{summary}", article.get("summary", ""))
    prompt = prompt.replace("{source}", article.get("source", "Unknown"))

    link = article.get("link", "") or ""
    pub_date = article.get("pub_date", "") or ""
    if hasattr(pub_date, "isoformat"):
        pub_date = pub_date.isoformat()

    prompt = prompt.replace("{link}", str(link))
    prompt = prompt.replace("{pub_date}", str(pub_date))

    resp = safe_request(prompt)
    raw = resp.choices[0].message.content

    try:
        return json.loads(raw)
    except Exception as e:
        logger.error(f"Failed to parse AI output for summarize_article: {e}")
        return {
            "title": "News Summary",
            "source": article.get("source", "Unknown"),
            "link": str(link),
            "pub_date": str(pub_date),
            "region": "global",
            "cn_summary": article.get("summary", ""),
            "en_summary": article.get("summary", ""),
            "cn_insights": [],
            "en_insights": [],
            "supply_chain": "",
            "nigeria_impact": "",
            "recommendation": ""
        }


# ============================================================
# 2) Price Impact Analysis (structured JSON)
# ============================================================
def analyze_price_impact(price_list: list[dict]) -> dict:
    """
    Input: price_list
    Output: JSON dict (rendered into HTML later)
    """
    prompt = load_prompt("analyze_price_impact")
    prompt = prompt.replace("{price_list}", json.dumps(price_list, ensure_ascii=False))

    resp = safe_request(prompt)
    raw = resp.choices[0].message.content

    try:
        return json.loads(raw)
    except Exception as e:
        logger.error(f"Failed to parse AI output for analyze_price_impact: {e}")
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
# 3) Daily Insight (structured JSON)
# ============================================================
def generate_daily_insight() -> dict:
    """
    Output: JSON dict (rendered into HTML later)
    """
    prompt = load_prompt("daily_insight")

    resp = safe_request(prompt)
    raw = resp.choices[0].message.content

    try:
        return json.loads(raw)
    except Exception as e:
        logger.error(f"Failed to parse AI output for daily_insight: {e}")
        return {
            "title": "Daily Insight",
            "points": [
                "AI output could not be parsed."
            ]
        }


# ============================================================
# 4) Safe AI Summary
# ============================================================
def safe_ai_summary(text: str) -> str:
    """
    Generate a faithful summary using safe_summary prompt.
    """
    base_prompt = load_prompt("safe_summary")

    final_prompt = f"""
{base_prompt}

正文内容（截断至 4000 字符）：
{text[:4000]}
"""

    result = summarize_article({"summary": final_prompt})
    return result.get("summary", "")


# ============================================================
# 5) Industry Detection
# ============================================================
def detect_industry(text: str) -> str:
    """
    Simple industry detection based on keywords.
    """
    t = text.lower()

    if any(k in t for k in ["硅料", "硅片", "组件", "光伏", "n型", "p型", "电池片"]):
        return "pv"
    if any(k in t for k in ["储能", "bess", "电池", "并网", "系统集成"]):
        return "bess"
    if any(k in t for k in ["逆变器", "inverter", "mppt", "效率"]):
        return "inverter"
    if any(k in t for k in ["电价", "tariff", "nerc", "ferc", "电力市场"]):
        return "power"
    if any(k in t for k in ["europe", "us", "germany", "uk", "海外", "出口"]):
        return "overseas"

    return "general"


# ============================================================
# 6) Safe AI Summary with Industry Context
# ============================================================
def safe_ai_summary_industry(text: str) -> str:
    """
    Generate industry-specific summary using industry_summary prompt.
    """
    industry = detect_industry(text)
    base_prompt = load_prompt("industry_summary")

    final_prompt = f"""
{base_prompt}

行业类型：{industry}

正文内容（截断至 4000 字符）：
{text[:4000]}
"""

    result = summarize_article({"summary": final_prompt})
    return result.get("summary", "")