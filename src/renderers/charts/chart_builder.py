import matplotlib.pyplot as plt
import pandas as pd
import os
import datetime
from pathlib import Path

from src.system.config_loader import load_config
from src.system.logger import setup_logger

config = load_config()
charts_dir = Path(config["paths"]["charts_dir"]).resolve()

logger = setup_logger("main")


def build_price_chart(history_file: str, output_path: str | None = None) -> str | None:
    """
    Build historical price line chart.
    :param history_file: Path to CSV file containing price history
    :param output_path: Optional path to save chart image. If None, auto-generate under src/runtime_output/charts
    :return: Path to generated chart file, or None if skipped
    """
    try:
        # Check file existence and non-empty
        if not os.path.exists(history_file) or os.path.getsize(history_file) == 0:
            logger.warning("History price file is missing or empty, skip chart generation.")
            return None

        df = pd.read_csv(history_file)

        # Check empty dataframe
        if df.empty:
            logger.warning("History price data is empty, skip chart generation.")
            return None

        # Check required columns
        required_cols = {"item", "date", "price"}
        if not required_cols.issubset(df.columns):
            logger.warning("History price file format invalid, skip chart generation.")
            return None

        # Ensure date column is datetime
        try:
            df["date"] = pd.to_datetime(df["date"])
        except Exception:
            logger.warning("Failed to parse 'date' column, using raw values.")

        # Plot chart
        plt.figure(figsize=(10, 5))
        for item in df["item"].unique():
            sub = df[df["item"] == item]
            plt.plot(sub["date"], sub["price"], label=item)

        plt.title("Historical Price Trends")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()

        # Determine output path
        if output_path is None:
            date_str = datetime.date.today().isoformat()
            output_path = charts_dir / f"price_chart_{date_str}.png"
        else:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            output_path = Path(output_path).resolve()

        # Save chart
        plt.savefig(output_path)
        plt.close()

        logger.info(f"Price chart generated: {output_path}")
        return str(output_path)

    except Exception as e:
        logger.error(f"Failed to generate price chart: {e}")
        return None