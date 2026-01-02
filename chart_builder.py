import matplotlib.pyplot as plt
import pandas as pd
import os

#  2.生成历史价格折现图
def build_price_chart(history_file, output_path):
    # === 新增：文件不存在或为空时直接跳过 ===
    if not os.path.exists(history_file) or os.path.getsize(history_file) == 0:
        print("[WARN] 历史价格文件为空，跳过图表生成")
        return

    df = pd.read_csv(history_file)

    # === 新增：如果 CSV 里没有数据，也跳过 ===
    if df.empty:
        print("[WARN] 历史价格数据为空，跳过图表生成")
        return

    # === 新增：如果缺少关键列，也跳过（防止格式错误）===
    required_cols = {"item", "date", "price"}
    if not required_cols.issubset(df.columns):
        print("[WARN] 历史价格文件格式不正确，跳过图表生成")
        return

    # === 原有逻辑保持完全不变 ===
    plt.figure(figsize=(10, 5))
    for item in df["item"].unique():
        sub = df[df["item"] == item]
        plt.plot(sub["date"], sub["price"], label=item)

    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()