import os
import json
import shutil
from datetime import datetime, date, timedelta


def make_json_safe(obj):
    """递归处理，将 date/datetime 转成字符串，其他保持不变"""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()

    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [make_json_safe(i) for i in obj]

    return obj


class DailyCache:
    def __init__(self, base_path="./cache", logger=None):
        self.base_path = base_path
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.day_path = os.path.join(base_path, self.today)
        self.logger = logger

        os.makedirs(self.day_path, exist_ok=True)

    def _file(self, name):
        return os.path.join(self.day_path, f"{name}.json")

    def exists(self, name):
        return os.path.exists(self._file(name))

    def load(self, name):
        with open(self._file(name), "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, name, data):
        safe_data = make_json_safe(data)
        with open(self._file(name), "w", encoding="utf-8") as f:
            json.dump(safe_data, f, ensure_ascii=False, indent=2)

    def clean_old_cache(self, keep_days=7):
        """自动清理超过 keep_days 的缓存目录"""
        cutoff = datetime.now() - timedelta(days=keep_days)

        # 如果 cache 目录不存在，直接返回
        if not os.path.exists(self.base_path):
            return

        for folder in os.listdir(self.base_path):
            folder_path = os.path.join(self.base_path, folder)

            if not os.path.isdir(folder_path):
                continue

            try:
                folder_date = datetime.strptime(folder, "%Y-%m-%d")
            except ValueError:
                continue

            if folder_date < cutoff:
                shutil.rmtree(folder_path)
                if self.logger:
                    self.logger.info(f"[Cache] Removed old cache folder: {folder}")