"""Logging setup."""

import logging.config


def setup_logging(debug: bool = False) -> None:
    """Log everything to stdout.

    Args:
        debug (bool): Log at DEBUG level instead of INFO.
    """
    level = "DEBUG" if debug else "INFO"
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "simple": {
                    "format": "%(asctime)s:%(levelname)8s:%(name)12s: %(message)s"
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": level,
                    "formatter": "simple",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {"level": level, "handlers": ["console"]},
            # the http libraries are far too chatty at DEBUG, our own logs are enough
            "loggers": {
                "httpx": {"level": "WARNING"},
                "httpcore": {"level": "WARNING"},
                "apscheduler": {"level": "INFO" if debug else "WARNING"},
            },
        }
    )
