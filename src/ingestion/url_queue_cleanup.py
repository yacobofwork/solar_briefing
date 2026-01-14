import json
from pathlib import Path
from datetime import datetime, timedelta
import shutil
import yaml
from src.system.logger import setup_logger

logger = setup_logger("main")

QUEUE_PATH = Path("src/data/incoming_urls.jsonl")
BACKUP_PATH = Path("src/data/incoming_urls_backup.jsonl")


def load_config() -> dict:
    """
    Load cleanup configuration from config.yaml.
    Returns default values if config file is missing.
    """
    config_path = Path("config.yaml")
    if not config_path.exists():
        logger.warning("Config file not found, using default cleanup settings.")
        return {"url_queue": {"retention_days": 7, "keep_pending": True, "if_backup": False}}

    try:
        with config_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config file: {e}")
        return {"url_queue": {"retention_days": 7, "keep_pending": True, "if_backup": False}}


def cleanup_url_queue() -> None:
    """
    Clean up the URL queue file:
    - Keep pending entries
    - Keep entries within retention_days
    - Optionally backup old file
    """
    if not QUEUE_PATH.exists():
        logger.info("Queue file does not exist, skipping cleanup.")
        return

    config = load_config().get("url_queue", {})
    retention_days = config.get("retention_days", 7)
    keep_pending = config.get("keep_pending", True)
    if_backup = config.get("if_backup", False)

    cutoff = datetime.now() - timedelta(days=retention_days)

    cleaned = []
    removed = []

    try:
        with QUEUE_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning("Skipping invalid JSON line in queue file.")
                    continue

                ts_raw = item.get("timestamp")
                status = item.get("status")

                # Always keep pending
                if keep_pending and status == "pending":
                    cleaned.append(item)
                    continue

                # If timestamp missing or invalid → keep
                if not isinstance(ts_raw, str):
                    cleaned.append(item)
                    continue
                try:
                    ts = datetime.fromisoformat(ts_raw)
                except Exception:
                    cleaned.append(item)
                    continue

                # Keep recent entries, remove old ones
                if ts >= cutoff:
                    cleaned.append(item)
                else:
                    removed.append(item)

        # Backup old file if enabled
        if if_backup:
            try:
                shutil.copy(QUEUE_PATH, BACKUP_PATH)
                logger.info(f"Backup created: {BACKUP_PATH}")
            except Exception as e:
                logger.error(f"Failed to create backup: {e}")

        # Write cleaned file
        with QUEUE_PATH.open("w", encoding="utf-8") as f:
            for item in cleaned:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        logger.info(f"Cleanup complete: kept {len(cleaned)} entries, removed {len(removed)} entries.")

    except Exception as e:
        logger.error(f"Failed to clean up queue file: {e}")