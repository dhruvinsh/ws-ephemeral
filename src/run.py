"""
Module that run the setup for windscrib's ephemeral port
"""
import logging
import time

from tqdm import trange

import config
from lib.qbit import QbitManager
from logger import setup_logging
from util import to_seconds
from ws import Windscribe

setup_logging()

logger = logging.getLogger("main")

# wait befor setting the ephemeral ports
DAYS: int = 7


def main() -> None:
    """Main function responsible for setting up ws and qbit.

    Steps:
    - login to ws
    - setup new matching ports
    - setup qbit
    """
    ws = Windscribe(username=config.WS_USERNAME, password=config.WS_PASSWORD)
    port = ws.setup()
    ws.close()

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
        logger.error("cannot able to work with qbit")
        raise
    qbit.set_listen_port(port)

    if config.QBIT_PRIVATE_TRACKER:
        qbit.setup_private_tracker()


while True:
    logger.info("setting the ephemeral port")
    main()

    logger.info("going to wait patiently for %s days befor next reset", DAYS)
    for _ in trange(to_seconds(DAYS)):
        time.sleep(1)
