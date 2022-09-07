"""
Module to setup logging
"""
import os
import logging

# logging setup
DEBUG: bool = bool(os.environ.get("WS_DEBUG"))
LEVEL: int = logging.DEBUG if DEBUG else logging.INFO

BASIC_FORMAT: str = "%(asctime)s:%(levelname)8s:%(name)s:%(message)s"

# setup basic logging format
logging.basicConfig(level=LEVEL, format=BASIC_FORMAT)


def create_logger(name: str = __name__, level: int = LEVEL) -> logging.Logger:
    """create logger based on given name else use default"""

    logger: logging.Logger = logging.getLogger(name)
    logger.setLevel(level)

    return logger
