import matplotlib.pyplot as plt
import pandas as pd


#  2.生成历史价格折现图
def build_price_chart(history_file, output_path):
    df = pd.read_csv(history_file)

    plt.figure(figsize=(10, 5))
    for item in df["item"].unique():
        sub = df[df["item"] == item]
        plt.plot(sub["date"], sub["price"], label=item)

    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()