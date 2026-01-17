# test_price_trend_chart.py

import matplotlib

matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import json
import os

# 模拟你的数据（来自 RAW AI OUTPUT）
TEST_DATA = {
    "dates": ["2026-01-11", "2026-01-12", "2026-01-13", "2026-01-14", "2026-01-15", "2026-01-16", "2026-01-17"],
    "pv": {
        "polysilicon_rmb_per_kg": [78.5, 78.5, 78.5, 78.5, 78.5, 78.5, 78.5],
        "silver_rmb_per_kg": [6120, 6120, 6120, 6210, 6210, 6210, 6250],
        "aluminum_rmb_per_ton": [19200, 19200, 19200, 19300, 19300, 19300, 19400]
    },
    "bess": {
        "lithium_carbonate_rmb_per_ton": [112000, 112000, 112000, 112000, 112000, 112000, 112000],
        "lithium_hydroxide_rmb_per_ton": [102000, 102000, 102000, 102000, 102000, 102000, 102000],
        "nickel_usd_per_ton": [17800, 17800, 17800, 17900, 17900, 18000, 18100],
        "cobalt_usd_per_ton": [32800, 32800, 32800, 32900, 32900, 33000, 33100]
    }
}


def _plot_from_data(data) -> str:
    """模拟 generate_price_trend_chart 的核心绘图逻辑"""
    dates = data["dates"]
    pv = data["pv"]
    bess = data["bess"]

    # PV 数据
    polysilicon = pv["polysilicon_rmb_per_kg"]
    silver = pv["silver_rmb_per_kg"]
    aluminum = [x / 1000 for x in pv["aluminum_rmb_per_ton"]]

    # BESS 数据
    lithium_carbonate = [x / 1000 for x in bess["lithium_carbonate_rmb_per_ton"]]
    lithium_hydroxide = [x / 1000 for x in bess["lithium_hydroxide_rmb_per_ton"]]
    nickel = bess["nickel_usd_per_ton"]
    cobalt = bess["cobalt_usd_per_ton"]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

    # === Upper: PV ===
    ax1.plot(dates, polysilicon, label='Polysilicon (RMB/kg)', marker='o', linewidth=2)
    ax1.plot(dates, silver, label='Silver (RMB/kg)', marker='s', linewidth=2)
    ax1.plot(dates, aluminum, label='Aluminum (RMB/ton ÷1000)', marker='^', linewidth=2)

    all_pv = polysilicon + silver + aluminum
    y_min = min(all_pv)
    y_max = max(all_pv)
    padding = (y_max - y_min) * 0.1 or 1
    ax1.set_ylim(y_min - padding, y_max + padding)
    ax1.set_title('Photovoltaic (PV) Raw Material Prices (Last 7 Days)', fontsize=13)
    ax1.set_ylabel('Price (RMB)')
    ax1.legend(loc='upper left')
    ax1.grid(True, linestyle='--', alpha=0.6)

    # === Lower: BESS ===
    ax2.plot(dates, lithium_carbonate, label='Lithium Carbonate (RMB/ton ÷1000)', marker='D', linewidth=2)
    ax2.plot(dates, lithium_hydroxide, label='Lithium Hydroxide (RMB/ton ÷1000)', marker='D', linestyle='--',
             linewidth=2)
    ax2.plot(dates, nickel, label='Nickel (USD/ton)', marker='v', linewidth=2)
    ax2.plot(dates, cobalt, label='Cobalt (USD/ton)', marker='*', linewidth=2)

    all_bess = lithium_carbonate + lithium_hydroxide + nickel + cobalt
    y_min = min(all_bess)
    y_max = max(all_bess)
    padding = (y_max - y_min) * 0.1 or 1
    ax2.set_ylim(y_min - padding, y_max + padding)
    ax2.set_title('Energy Storage (BESS) Raw Material Prices (Last 7 Days)', fontsize=13)
    ax2.set_ylabel('Price')
    ax2.set_xlabel('Date')
    ax2.legend(loc='upper left')
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Save to base64 and file
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.savefig("test_price_trend.png")  # ← 人工检查用
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


if __name__ == "__main__":
    print("🧪 正在生成价格趋势图...")
    b64_str = _plot_from_data(TEST_DATA)

    print(f"✅ 图表已保存为: {os.path.abspath('test_price_trend.png')}")
    print(f"📊 Base64 长度: {len(b64_str)} 字符")

    # 可选：生成 HTML 预览
    with open("test_preview.html", "w") as f:
        f.write(f'''
        <html><body>
        <h2>Test: Price Trend Chart</h2>
        <img src="data:image/png;base64,{b64_str}" style="max-width:100%;">
        </body></html>
        ''')
    print(f"🌐 HTML 预览: {os.path.abspath('test_preview.html')}")