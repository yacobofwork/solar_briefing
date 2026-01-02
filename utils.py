import logging
from datetime import datetime
import re


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def setup_logger(name="app"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 避免重复添加 handler
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            "%Y-%m-%d %H:%M:%S"
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)

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