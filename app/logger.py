from __future__ import annotations

import logging
from pathlib import Path

from rich.logging import RichHandler

from app.config import BASE_DIR


LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "app.log"

'''
统一 日志工厂函数
observability: 用log追踪系统问题，定位；记录LLM输入输出

--不关心数据--
'''
def setup_logger(name: str = "resume_tailoring") -> logging.Logger:
    """
    Create and return a configured logger.

    Features:
    - Rich console logging for local development
    - File logging for debugging/history
    - Prevent duplicate handlers
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler with rich formatting
    console_handler = RichHandler(rich_tracebacks=True)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # File handler
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger