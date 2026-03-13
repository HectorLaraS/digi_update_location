from __future__ import annotations

import logging
from pathlib import Path


def setup_logging(log_dir: Path, log_file_name: str, log_level: str) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file_path = log_dir / log_file_name

    logger = logging.getLogger("digi_location_manager")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False

    logger.info("Logging initialized successfully.")
    logger.info("Log file path: %s", log_file_path)

    return logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"digi_location_manager.{name}")