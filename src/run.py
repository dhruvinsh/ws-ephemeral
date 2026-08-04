"""
Module that run the setup for windscrib's ephemeral port
"""

import logging
import time

import schedule

import config
from lib.gluetun import GluetunManager
from lib.qbit import QbitManager
from logger import setup_logging
from monitor import HEARTBEAT, monitor
from util import catch_exceptions
from ws import Windscribe

setup_logging()

logger = logging.getLogger("main")


@catch_exceptions(cancel_on_failure=False)
def main() -> None:
    """Main function responsible for setting up ws and qbit.

    Steps:
    - check if the heartbeat was okay
    - login to ws
    - setup new matching ports
    - update Gluetun's VPN firewall, if configured
    - setup qbit
    """
    if not HEARTBEAT:
        msg = (
            "From heartbeat check, "
            "qBitTorrent wasn't accessible. "
            "Can't run ephemeral renewal right now."
        )
        logger.error(msg)
        return

    logger.info("Running automation...")
    with Windscribe(
        username=config.WS_USERNAME, password=config.WS_PASSWORD, totp=config.WS_TOTP
    ) as ws:
        port = ws.setup()

    if config.GLUETUN_URL:
        with GluetunManager(
            url=config.GLUETUN_URL,
            timeout=config.REQUEST_TIMEOUT,
            api_key=config.GLUETUN_API_KEY,
            username=config.GLUETUN_USERNAME,
            password=config.GLUETUN_PASSWORD,
        ) as gluetun:
            gluetun.set_forwarded_port(port)

    if not config.qbit_found:
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
            api_key=config.QBIT_API_KEY,
        )
    except Exception:
        logger.error("not able to work with qbit")
        raise
    qbit.set_listen_port(port)

    if config.QBIT_PRIVATE_TRACKER:
        qbit.setup_private_tracker()
    logger.info("Port setup completed..")


if __name__ == "__main__":
    schedule.every(config.DAYS).days.at(config.TIME).do(main)
    schedule.every(5).minutes.do(monitor)
    schedule.run_all()

    if not config.ONESHOT:
        logger.info(
            f"Schedule is setup to run every {config.DAYS} day at {config.TIME}"
        )
        while True:
            schedule.run_pending()
            time.sleep(1)
