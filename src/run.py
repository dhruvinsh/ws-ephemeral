"""
Module that run the setup for windscrib's ephemeral port
"""

import logging
import time
import datetime

import schedule

import config
from lib.qbit import QbitManager
from logger import setup_logging
from monitor import HEARTBEAT, monitor
from util import catch_exceptions
from ws import Windscribe, PortManager

setup_logging()

logger = logging.getLogger("main")


@catch_exceptions(cancel_on_failure=False)
def main() -> None:
    """Main function responsible for setting up ws and qbit.

    Steps:
    - check if the port is still valid
    - login to ws (if needed)
    - setup new matching ports (if needed)
    - check if the hearbeat was okay
    - setup qbit
    """
    try:
        port_manager = PortManager.deserialize_from_env(config.WS_ENVFILE)
        if port_manager and not port_manager.is_expired():
            expiration_time = port_manager.expiration_time.strftime('%Y-%m-%d %H:%M:%S')
            logger.debug("Port %d is still valid until %s, skipping update...", port_manager.port, expiration_time)
            return
        else:
            logger.info("Port expired (or about to expire), reallocating a new port...")
    except Exception as e:
        logger.warning(f"PortManager deserialization failed: {e}")
        logger.info("Reallocating a new port...")

    logger.info("Running automation...")
    with Windscribe(
        username=config.WS_USERNAME, password=config.WS_PASSWORD, totp=config.WS_TOTP
    ) as ws:
        port_manager = ws.setup()
        port_manager.serialize_to_env(config.WS_ENVFILE)

    if not HEARTBEAT:
        msg = (
            "From hearbeat check, "
            "qBitTorrent wasn't accesible. "
            "Can't run ephemeral renewal right now."
        )
        logger.error(msg)
        return

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
    qbit.set_listen_port(port_manager.get_port())

    if config.QBIT_PRIVATE_TRACKER:
        qbit.setup_private_tracker()
    logger.info("Port setup completed..")


if __name__ == "__main__":
    schedule.every(5).minutes.do(main)
    schedule.every(5).minutes.do(monitor)
    schedule.run_all()

    if not config.ONESHOT:
        logger.info(
            f"Schedule is setup to run every {config.DAYS} day at {config.TIME}"
        )
        while True:
            schedule.run_pending()
            time.sleep(1)
