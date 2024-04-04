"""Module that run the setup for windscrib's ephemeral port."""

from __future__ import annotations

import logging
import time

import config
import schedule
from lib.qbit import QbitManager
from logger import setup_logging
from monitor import HEARTBEAT, monitor
from util import catch_exceptions
from ws import Windscribe

setup_logging()

logger = logging.getLogger("main")


@catch_exceptions(cancel_on_failure=False)
def main() -> dict[str, str | None | int]:
    """Set up ws and qbit.

    Steps:
    - check if the hearbeat was okay
    - login to ws
    - setup new matching ports
    - setup qbit
    """
    if not HEARTBEAT:
        msg = (
            "From hearbeat check, "
            "qBitTorrent wasn't accesible. "
            "Can't run ephemeral renewal right now."
        )
        logger.error(msg)
        return {"status": False, "reason": "heartbeat failure", "port": None}

    logger.info("Running automation...")
    with Windscribe(username=config.WS_USERNAME, password=config.WS_PASSWORD) as ws:
        port = ws.setup()

    if not config.QBIT_FOUND:
        logger.warning(
            "Read the latest doc: https://github.com/dhruvinsh/ws-ephemeral#readme",
        )
        return {"status": True, "reason": "no qbit but port updated", "port": port}

    try:
        qbit = QbitManager(
            host=config.QBIT_HOST,
            port=config.QBIT_PORT,
            username=config.QBIT_USERNAME,
            password=config.QBIT_PASSWORD,
        )
    except Exception:
        logger.exception("not able to work with qbit")
        raise
    qbit.set_listen_port(port)

    if config.QBIT_PRIVATE_TRACKER:
        qbit.setup_private_tracker()
    logger.info("Port setup completed..")
    return {"status": True, "reason": "", "port": port}


if __name__ == "__main__":
    schedule.every(config.DAYS).days.at(config.TIME).do(main)
    schedule.every(5).minutes.do(monitor)
    schedule.run_all()

    if not config.ONESHOT:
        logger.info(
            "Schedule is setup to run every %s day at %s",
            config.DAYS,
            config.TIME,
        )
        while True:
            schedule.run_pending()
            time.sleep(1)
