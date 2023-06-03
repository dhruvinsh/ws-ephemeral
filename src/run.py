"""
Module that run the setup for windscrib's ephemeral port
"""
import logging
import time

import schedule

import config
from lib.qbit import QbitManager
from logger import setup_logging
from util import catch_exceptions
from ws import Windscribe

setup_logging()

logger = logging.getLogger("main")

# wait befor setting the ephemeral ports
DAYS: int = 6
TIME: str = "02:00"


@catch_exceptions(cancel_on_failure=False)
def main() -> None:
    """Main function responsible for setting up ws and qbit.

    Steps:
    - login to ws
    - setup new matching ports
    - setup qbit
    """
    logger.info("Running automation...")
    with Windscribe(username=config.WS_USERNAME, password=config.WS_PASSWORD) as ws:
        port = ws.setup()

    if not config.QBIT_FOUND:
        logger.warning(
            "Read the latest doc: https://github.com/dhruvinsh/ws-ephemeral#readme"
        )
        return

    try:
        qbit = QbitManager(
            host=config.QBIT_HOST,
            port=config.QBIT_PORT,
            username=config.QBIT_USERNAME,
            password=config.QBIT_PASSWORD,
        )
    except Exception:
        logger.error("not able to work with qbit")
        raise
    qbit.set_listen_port(port)

    if config.QBIT_PRIVATE_TRACKER:
        qbit.setup_private_tracker()
    logger.info("Port setup completed..")


if __name__ == "__main__":
    schedule.every(DAYS).days.at(TIME).do(main)
    schedule.run_all()

    logger.info(f"Schedule is setup to run every {DAYS} day at {TIME}")
    while True:
        schedule.run_pending()
        time.sleep(1)
