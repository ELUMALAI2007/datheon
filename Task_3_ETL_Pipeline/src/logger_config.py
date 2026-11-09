import logging
import sys
from pathlib import Path


def setup_logger(log_file_path: Path, log_level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a centralized logger with dual output:
    1. Rotating or appended log file in logs/pipeline.log
    2. Formatted colored console output
    """
    logger = logging.getLogger("DatheonETLPipeline")
    logger.setLevel(log_level)

    # Avoid adding duplicate handlers if logger was already created
    if logger.handlers:
        return logger

    # Ensure log directory exists
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Formatter
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)-8s] [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File Handler
    file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

