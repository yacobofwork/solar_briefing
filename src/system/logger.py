import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler

def setup_logger(name="main", config=None):
    """
    Centralized logger: only 'main' writes to file, others go to console.
    """
    logger = logging.getLogger("main")  # Force all modules to use 'main'
    if logger.handlers:
        return logger

    # Load config if available
    log_level = "DEBUG"
    logs_dir = Path("src/logs").resolve()
    if config:
        log_level = config.get("logging", {}).get("level", "DEBUG").upper()
        logs_dir = Path(config["paths"]["logs_dir"]).resolve()

    logs_dir.mkdir(parents=True, exist_ok=True)
    logger.setLevel(getattr(logging, log_level, logging.DEBUG))

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (only once, for 'main')
    file_handler = TimedRotatingFileHandler(
        filename=logs_dir / "main.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger