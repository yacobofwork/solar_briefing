import logging
from datetime import datetime
import re
import os


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_env(key, default=None, required=False):
    value = os.getenv(key, default)
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value

def setup_logger(name="app"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # 控制台输出
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            "%Y-%m-%d %H:%M:%S"
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # 文件日志（可选）
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")

        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

#  增强版清洗：去掉换行、HTML、Markdown、重复空格
def clean_html(text: str) -> str:

    if not text:
        return ""

    # 去掉 HTML 标签
    text = re.sub(r"<[^>]+>", " ", text)

    # 去掉 Markdown 代码块 ```
    text = text.replace("```", " ")

    # 去掉 Markdown 粗体/斜体符号
    text = text.replace("**", " ").replace("*", " ")

    # 替换换行
    text = text.replace("\n", " ")

    # 合并重复空格
    text = re.sub(r"\s+", " ", text)

    return text.strip()