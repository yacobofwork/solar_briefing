import os
import pandas as pd
from src.system.logger import setup_logger

logger = setup_logger("main")


def save_price_history(prices: list[dict], history_file: str) -> None:
    """
    Save daily price data into history CSV file.
    Ensures correct headers, merges with existing data, and sorts by date.
    """
    if not prices:
        logger.warning("No price data today, skipping history update.")
        return

    # Ensure correct column order
    df_new = pd.DataFrame(prices, columns=["item", "date", "price"])
    missing = {"item", "date", "price"} - set(df_new.columns)
    if missing:
        logger.error(f"Missing required columns in prices : {missing}")

    try:
        # If file does not exist → create new
        if not os.path.exists(history_file) or os.path.getsize(history_file) == 0:
            df_new.to_csv(history_file, index=False)
            logger.info(f"Created new history file: {history_file}")
            return

        # Read old data
        df_old = pd.read_csv(history_file)

        # Fix missing columns
        required_cols = {"item", "date", "price"}
        if not required_cols.issubset(df_old.columns):
            logger.warning("History file format invalid, resetting headers.")
            df_old = pd.DataFrame(columns=["item", "date", "price"])

        # Merge
        df_all = pd.concat([df_old, df_new], ignore_index=True)

        # Ensure date column is datetime
        df_all["date"] = pd.to_datetime(df_all["date"], errors="coerce")

        # Drop rows with invalid dates
        df_all = df_all.dropna(subset=["date"])

        # Sort by date ascending
        df_all = df_all.sort_values(by="date")

        # Drop duplicates (same item + date)
        df_all = df_all.drop_duplicates(subset=["item", "date"], keep="last")

        # Write back
        df_all.to_csv(history_file, index=False)
        logger.info(f"Updated history file: {history_file} with {len(df_new)} new records.")

    except Exception as e:
        logger.error(f"Failed to update price history: {e}")