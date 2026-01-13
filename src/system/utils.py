from datetime import datetime
import re
import os
from dotenv import load_dotenv

# Explicitly load environment variables from src/config/.env
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # points to src/
CONFIG_DIR = os.path.join(BASE_DIR, "config")
ENV_PATH = os.path.join(CONFIG_DIR, ".env")

load_dotenv(dotenv_path=ENV_PATH)


def now_str(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Return current timestamp as string."""
    return datetime.now().strftime(fmt)


def get_env(key: str, default=None, required: bool = False):
    """
    Retrieve environment variable value.
    :param key: Environment variable name
    :param default: Default value if not set
    :param required: If True and variable is missing, raise RuntimeError
    :return: Environment variable value or default
    """
    value = os.getenv(key, default)
    if required and value is None:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


def clean_html(text: str) -> str:
    """
    Clean HTML/Markdown from text.
    - Remove HTML tags
    - Remove Markdown symbols
    - Normalize whitespace
    """
    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove Markdown code blocks and symbols
    text = re.sub(r"```", " ", text)
    text = re.sub(r"[*_#>`~]", " ", text)

    # Replace newlines with space
    text = text.replace("\n", " ")

    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()