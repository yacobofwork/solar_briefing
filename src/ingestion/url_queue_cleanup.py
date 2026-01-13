import json
from pathlib import Path
from datetime import datetime, timedelta
import shutil
import yaml

QUEUE_PATH = Path("data/incoming_urls.jsonl")
BACKUP_PATH = Path("data/incoming_urls_backup.jsonl")


def load_config():
    config_path = Path("config.yaml")
    if not config_path.exists():
        return {"url_queue": {"retention_days": 7, "keep_pending": True}}
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def cleanup_url_queue():
    if not QUEUE_PATH.exists():
        print("[url_queue] 队列文件不存在，跳过清理。")
        return

    config = load_config().get("url_queue", {})
    retention_days = config.get("retention_days", 7)
    keep_pending = config.get("keep_pending", True)

    cutoff = datetime.now() - timedelta(days=retention_days)

    cleaned = []
    removed = []

    with QUEUE_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                item = json.loads(line)
            except:
                continue

            ts_raw = item.get("timestamp")
            # 如果 timestamp 缺失或不是字符串，直接保留该记录
            if not isinstance(ts_raw, str):
                cleaned.append(item)
                continue
            try:
                ts = datetime.fromisoformat(ts_raw)
            except Exception:
                # 如果格式不对，也保留
                cleaned.append(item)
                continue

            status = item.get("status")

            # 永远保留 pending
            if keep_pending and status == "pending":
                cleaned.append(item)
                continue

            # 保留最近 N 天
            if ts >= cutoff:
                cleaned.append(item)
            else:
                removed.append(item)

    # 备份旧文件
    if_backup = config.get("if_backup", False)
    if if_backup:
        shutil.copy(QUEUE_PATH, BACKUP_PATH)

    # 写入新文件
    with QUEUE_PATH.open("w", encoding="utf-8") as f:
        for item in cleaned:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"[url_queue] 清理完成：保留 {len(cleaned)} 条，删除 {len(removed)} 条。")