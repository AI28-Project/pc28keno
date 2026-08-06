"""
日志工具 - 统一日志格式
"""

import logging
import sys

from shared.config import LOG_LEVEL


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志实例"""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
        logger.propagate = False

    return logger

