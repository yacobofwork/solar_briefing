import os
import re
import time
import json
from ast import Bytes
from pathlib import Path
from typing import IO

# Replace OpenAI with DashScope
from dashscope import Generation

from src.system.utils import get_env
from src.system.logger import setup_logger
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime

logger = setup_logger("main")


def _generate_error_chart(message: str) -> str:
    """生成错误占位图"""
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.text(0.5, 0.5, f"Chart Error:\n{message}",
            ha='center', va='center', fontsize=12, color='red')
    ax.axis('off')
    buf = Bytes
    IO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


def generate_price_trend_chart() -> str:
    """
    Fetch 14-day price trends for PV and BESS raw materials via Qwen,
    generate annotated dual-subplot chart, return as base64 PNG.

    Returns:
        str: base64-encoded PNG image string
    """
    try:
        # === Step 1: 构建 Prompt ===
        prompt_template = load_prompt("price_trend_query")  # 确保该文件要求14天
        today = datetime.now().strftime("%Y-%m-%d")
        prompt = prompt_template.replace("{{today}}", today)

        # === Step 2: 调用 Qwen 获取数据 ===
        raw_response = qwen_call(prompt, enable_search=True)

        # === Step 3: 解析 JSON 数据 ===
        data = json.loads(raw_response)

        dates = data["dates"]
        pv = data["pv"]
        bess = data["bess"]

        if len(dates) == 0:
            raise ValueError("No date data returned")

        # === Step 4: 准备数据 ===
        # PV 材料
        polysilicon = pv["polysilicon_rmb_per_kg"]
        silver = pv["silver_rmb_per_kg"]
        aluminum = [x / 1000 for x in pv["aluminum_rmb_per_ton"]]  # RMB/ton → scaled

        # BESS 材料
        lithium_carbonate = [x / 1000 for x in bess["lithium_carbonate_rmb_per_ton"]]
        lithium_hydroxide = [x / 1000 for x in bess["lithium_hydroxide_rmb_per_ton"]]
        nickel = bess["nickel_usd_per_ton"]
        cobalt = bess["cobalt_usd_per_ton"]

        # === Step 5: 计算14天涨跌幅 ===
        def calc_change(series):
            if not series or len(series) < 2 or series[0] == 0:
                return 0.0
            return (series[-1] - series[0]) / series[0] * 100

        # PV changes
        silver_change = calc_change(silver)
        poly_change = calc_change(polysilicon)
        alum_change = calc_change(aluminum)

        # BESS changes
        lc_change = calc_change(lithium_carbonate)
        lh_change = calc_change(lithium_hydroxide)
        ni_change = calc_change(nickel)
        co_change = calc_change(cobalt)

        # === Step 6: 绘图 ===
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 11), sharex=True)

        # ------------------ Upper Plot: PV ------------------
        ax1.plot(dates, polysilicon, label='Polysilicon (RMB/kg)', marker='o', linewidth=2, markersize=5)
        ax1.plot(dates, silver, label='Silver (RMB/kg)', marker='s', linewidth=2, markersize=5)
        ax1.plot(dates, aluminum, label='Aluminum (RMB/ton ÷1000)', marker='^', linewidth=2, markersize=5)

        # 自动 Y 轴（使用 min/max + padding，避免百分位数过度裁剪）
        all_pv = polysilicon + silver + aluminum
        y_min = min(all_pv)
        y_max = max(all_pv)
        padding = (y_max - y_min) * 0.1 if (y_max - y_min) > 0 else 1.0
        ax1.set_ylim(y_min - padding, y_max + padding)

        # 添加 PV 标注框
        pv_text = (
            f"14-Day Change:\n"
            f"• Silver: {silver_change:+.1f}%\n"
            f"• Polysilicon: {poly_change:+.1f}%\n"
            f"• Aluminum: {alum_change:+.1f}%"
        )
        ax1.text(0.02, 0.98, pv_text,
                 transform=ax1.transAxes,
                 fontsize=9,
                 verticalalignment='top',
                 bbox=dict(boxstyle="round,pad=0.4", facecolor="#e6f7ff", edgecolor="#1890ff", alpha=0.85))

        ax1.set_title('Photovoltaic (PV) Raw Material Prices (Last 14 Days)', fontsize=13, pad=15)
        ax1.set_ylabel('Price (RMB)', fontsize=11)
        ax1.legend(loc='upper right')
        ax1.grid(True, linestyle='--', alpha=0.6)

        # ------------------ Lower Plot: BESS ------------------
        ax2.plot(dates, lithium_carbonate, label='Lithium Carbonate (RMB/ton ÷1000)', marker='D', linewidth=2,
                 markersize=5)
        ax2.plot(dates, lithium_hydroxide, label='Lithium Hydroxide (RMB/ton ÷1000)', marker='D', linestyle='--',
                 linewidth=2, markersize=5)
        ax2.plot(dates, nickel, label='Nickel (USD/ton)', marker='v', linewidth=2, markersize=5)
        ax2.plot(dates, cobalt, label='Cobalt (USD/ton)', marker='*', linewidth=2, markersize=5)

        all_bess = lithium_carbonate + lithium_hydroxide + nickel + cobalt
        y_min = min(all_bess)
        y_max = max(all_bess)
        padding = (y_max - y_min) * 0.1 if (y_max - y_min) > 0 else 1.0
        ax2.set_ylim(y_min - padding, y_max + padding)

        # 添加 BESS 标注框
        bess_text = (
            f"14-Day Change:\n"
            f"• Lithium Carbonate: {lc_change:+.1f}%\n"
            f"• Lithium Hydroxide: {lh_change:+.1f}%\n"
            f"• Nickel: {ni_change:+.1f}%\n"
            f"• Cobalt: {co_change:+.1f}%"
        )
        ax2.text(0.02, 0.98, bess_text,
                 transform=ax2.transAxes,
                 fontsize=9,
                 verticalalignment='top',
                 bbox=dict(boxstyle="round,pad=0.4", facecolor="#f6ffed", edgecolor="#52c41a", alpha=0.85))

        ax2.set_title('Energy Storage (BESS) Raw Material Prices (Last 14 Days)', fontsize=13, pad=15)
        ax2.set_ylabel('Price', fontsize=11)
        ax2.set_xlabel('Date', fontsize=11)
        ax2.legend(loc='upper right')
        ax2.grid(True, linestyle='--', alpha=0.6)

        # 格式化 X 轴
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        # === Step 7: 转为 base64 ===
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        logger.info("✅ Price trend chart generated successfully.")
        return img_base64

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
        return _generate_error_chart("Invalid JSON from AI")
    except KeyError as e:
        logger.error(f"Missing key in data: {e}")
        return _generate_error_chart("Incomplete data structure")
    except Exception as e:
        logger.error(f"Unexpected error in chart generation: {e}")
        return _generate_error_chart(str(e)[:100])


# ============================================================
# Qwen API Call Wrapper (Replaces DeepSeek)
# ============================================================
def qwen_call(prompt: str, enable_search: bool = False):
    """
    Invoke Qwen API via DashScope with retry logic, proxy handling, and input sanitization.

    Args:
        prompt (str): The user prompt to send to the model.
        enable_search (bool): Whether to enable web search during inference.

    Returns:
        str: The content returned by the model.

    Raises:
        RuntimeError: If all retries fail or response format is invalid.
    """
    api_key = get_env("DASHSCOPE_API_KEY", required=True)

    # 🔒 Save and clear proxy environment variables to ensure direct connection to DashScope (critical!)
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy']
    original_proxies = {k: os.environ.get(k) for k in proxy_vars}
    for k in proxy_vars:
        if k in os.environ:
            del os.environ[k]

    # 🧹 Sanitize prompt: remove HTML tags and non-printable control characters
    clean_prompt = re.sub(r'<[^>]+>', '', prompt)  # Remove HTML tags
    clean_prompt = ''.join(
        c for c in clean_prompt
        if ord(c) >= 32 or c in '\n\t'  # Keep printable characters + newline/tab
    ).strip()

    logger.debug(f"Calling Qwen (model=qwen-plus, search={enable_search}) with prompt length: {len(clean_prompt)}")

    for attempt in range(3):
        try:
            response = Generation.call(
                model="qwen-plus",
                messages=[{"role": "user", "content": clean_prompt}],
                enable_search=enable_search,
                result_format="message",
                api_key=api_key,
                timeout=30
            )

            # Check if valid content was returned
            if (hasattr(response, 'output') and
                    response.output and
                    hasattr(response.output, 'choices') and
                    response.output.choices and
                    hasattr(response.output.choices[0], 'message') and
                    response.output.choices[0].message.content):

                content = response.output.choices[0].message.content
                logger.debug(f"Qwen call succeeded on attempt {attempt + 1}")

                # 🔁 Restore original proxy settings (to avoid affecting other network operations)
                for k, v in original_proxies.items():
                    if v is not None:
                        os.environ[k] = v

                return content

            else:
                error_msg = f"Unexpected response format: code={getattr(response, 'code', 'N/A')}, message={getattr(response, 'message', 'N/A')}"
                logger.warning(f"Qwen format error (attempt {attempt + 1}): {error_msg}")
                if attempt < 2:
                    time.sleep(2)
                else:
                    raise RuntimeError(error_msg)

        except Exception as e:
            logger.error(f"Final Qwen failure details: {str(e)}", exc_info=True)
            if attempt < 2:
                time.sleep(2)
            else:
                # 🔁 Restore proxy even on final failure
                for k, v in original_proxies.items():
                    if v is not None:
                        os.environ[k] = v
                raise RuntimeError(f"Qwen failed after 3 retries: {str(e)}")

    # 🔁 Fallback: restore proxy (should not be reached under normal conditions)
    for k, v in original_proxies.items():
        if v is not None:
            os.environ[k] = v
    raise RuntimeError("Unexpected exit from qwen_call")


def load_prompt(name: str) -> str:

    project_root = Path(__file__).resolve().parents[1]  # Navigate back to src/
    prompt_path = project_root / "prompts" / f"{name}.txt"

    if not prompt_path.exists():
        logger.error(f"Prompt file not found: {prompt_path}")
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    with prompt_path.open("r", encoding="utf-8") as f:
        return f.read()


# ============================================================
# 1) News Summary — No web search needed (static content)
# ============================================================
def summarize_article(article: dict) -> dict:
    """
    Generate a structured summary of a news article using Qwen (no web search).
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

    # ❌ Disable web search (news content is already fetched)
    raw = qwen_call(prompt, enable_search=False)

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
# 2) Price Impact Analysis — ✅ Enable web search!
# ============================================================
def analyze_price_impact(price_list: list[dict]) -> dict:
    """
    Analyze solar component price fluctuations using real-time web search.
    """
    prompt = load_prompt("analyze_price_impact")
    prompt = prompt.replace("{price_list}", json.dumps(price_list, ensure_ascii=False))

    # ✅ Enable web search to explain price drivers (e.g., policy, supply chain, FX)
    raw = qwen_call(prompt, enable_search=True)

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
# 3) Daily Insight — ✅ Enable web search!
# ============================================================
def generate_daily_insight() -> dict:
    """
    Generate daily industry insights using up-to-date web information.
    """
    prompt = load_prompt("daily_insight")

    # ✅ Enable web search to fetch latest developments, policies, and global events
    raw = qwen_call(prompt, enable_search=True)

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
# 4 & 6) Safe Summaries — No web search needed
# ============================================================
def safe_ai_summary(text: str) -> str:
    """
    Generate a safe, truncated summary for arbitrary text (fallback behavior).
    """
    base_prompt = load_prompt("safe_summary")
    final_prompt = f"{base_prompt}\n\nMain content (truncated to 4000 characters):\n{text[:4000]}"
    result = summarize_article({"summary": final_prompt})
    return result.get("summary", "")


def detect_industry(text: str) -> str:
    """
    Heuristically detect the industry category based on keywords in the text.
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


def safe_ai_summary_industry(text: str) -> str:
    """
    Generate an industry-aware safe summary.
    """
    industry = detect_industry(text)
    base_prompt = load_prompt("industry_summary")
    final_prompt = f"{base_prompt}\n\nIndustry type: {industry}\n\nMain content (truncated to 4000 characters):\n{text[:4000]}"
    result = summarize_article({"summary": final_prompt})
    return result.get("summary", "")