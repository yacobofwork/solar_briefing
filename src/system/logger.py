import logging
import sys

def setup_logger(name="solar_briefing", config=None):
    """
    Initialize logging system with English-only output.
    :param name: logger name (string)
    :param config: optional configuration object (e.g., ConfigLoader instance)
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # English-only formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)

    # Avoid duplicate handlers
    if not logger.handlers:
        logger.addHandler(console_handler)

    # Apply log level from config if available
    if config and hasattr(config, "get"):
        log_level = config.get("LOG_LEVEL", "DEBUG").upper()
        logger.setLevel(getattr(logging, log_level, logging.DEBUG))

    return logger