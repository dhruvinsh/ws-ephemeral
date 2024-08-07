"""Collection of the jobs to run."""

import time

import schedule
from loguru import logger

from ws_ephemeral.cfg import config
from ws_ephemeral.cli import renew


def jobs() -> None:
    """Windscribe port renwal job."""
    schedule.every(config.DAYS).days.at(config.TIME).do(renew)
    schedule.run_all()

    if not config.ONESHOT:
        logger.info(f"Schedule is setup to run every {config.DAYS} day at {config.TIME}")
        while True:
            schedule.run_pending()
            time.sleep(1)
