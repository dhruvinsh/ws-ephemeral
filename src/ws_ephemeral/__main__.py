"""Run windscribe ephemeral."""

import sys

from loguru import logger

from ws_ephemeral.cfg import config
from ws_ephemeral.cli import cli

logger.remove(0)
logger.add(sys.stdout, level="DEBUG" if config.DEBUG else "INFO", format="{time} | {level: <8} | {message}")


if __name__ == "__main__":
    cli()
