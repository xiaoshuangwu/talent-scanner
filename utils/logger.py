"""日志工具"""

import os
import sys
from datetime import datetime
from loguru import logger


def setup_logger(config, verbose=False):
    """配置 loguru 日志"""
    logger.remove()  # 移除默认handler

    log_dir = config.get("global.log_dir", "./logs")
    os.makedirs(log_dir, exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"scanner_{date_str}.log")

    # 文件日志 - 详细
    logger.add(
        log_file,
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}"
    )

    # 控制台日志
    logger.add(
        sys.stderr,
        level="DEBUG" if verbose else "INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        colorize=True
    )

    return logger
