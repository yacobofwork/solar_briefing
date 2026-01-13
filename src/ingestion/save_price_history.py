import os
import pandas as pd

def save_price_history(prices, history_file):
    # 如果没有抓到价格，不写入空文件
    if not prices:
        print("[WARN] 今日无价格数据，不更新历史记录")
        return

    # 明确指定字段顺序，确保表头正确
    df_new = pd.DataFrame(prices, columns=["item", "date", "price"])

    # 如果文件不存在 → 创建并写入表头
    if not os.path.exists(history_file):
        df_new.to_csv(history_file, index=False)
        return

    # 如果文件存在但为空 → 写入表头
    if os.path.getsize(history_file) == 0:
        df_new.to_csv(history_file, index=False)
        return

    # 文件存在且有内容 → 读取旧数据
    df_old = pd.read_csv(history_file)

    # 如果旧文件缺少字段 → 强制修复
    required_cols = {"item", "date", "price"}
    if not required_cols.issubset(df_old.columns):
        print("[WARN] 历史文件格式错误，已自动修复表头")
        df_old = pd.DataFrame(columns=["item", "date", "price"])

    # 合并
    df_all = pd.concat([df_old, df_new], ignore_index=True)

    # 按日期排序（升序）
    df_all["date"] = pd.to_datetime(df_all["date"])
    df_all = df_all.sort_values(by="date")

    # 写回 CSV
    df_all.to_csv(history_file, index=False)