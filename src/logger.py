"""
Module to setup logging
"""
import logging
import os

# logging setup
DEBUG: bool = bool(os.environ.get("WS_DEBUG"))
LEVEL: int = logging.DEBUG if DEBUG else logging.INFO

BASIC_FORMAT: str = "%(asctime)s:%(levelname)8s:%(name)5s:%(message)s"


def create_logger(
    name: str = __name__, level: int = LEVEL, formatter: str = BASIC_FORMAT
) -> logging.Logger:
    """create logger based on given name else use default

    :param name: set logger name, default __name__
    :parma level: set log level, default INFO
    :param formatter: set streamHandler format,
                    default %(asctime)s:%(levelname)8s:%(name)s:%(message)s
    """

    logger_formatter = logging.Formatter(formatter)

    logger: logging.Logger = logging.getLogger(name)
    logger.setLevel(level)

    stream = logging.StreamHandler()
    stream.setLevel(level)
    stream.setFormatter(logger_formatter)

    logger.addHandler(stream)

    return logger
