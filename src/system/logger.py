import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler

def setup_logger(name="solar_briefing", config=None):
    """
    Initialize logging system with English-only output.
    Console + daily rotating file handler under src/logs.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # English-only formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    # Avoid duplicate handlers
    if not logger.handlers:
        logger.addHandler(console_handler)

        # File handler (daily rotation)
        logs_dir = Path("src/logs").resolve()
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = logs_dir / f"{name}.log"

        file_handler = TimedRotatingFileHandler(
            filename=log_file,
            when="midnight",   # 每天切分
            interval=1,
            backupCount=30,    # 保留30天
            encoding="utf-8"
        )
        file_handler.suffix = "%Y-%m-%d"
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Apply log level from config if available
    if config and hasattr(config, "get"):
        log_level = config.get("LOG_LEVEL", "DEBUG").upper()
        logger.setLevel(getattr(logging, log_level, logging.DEBUG))

    return logger