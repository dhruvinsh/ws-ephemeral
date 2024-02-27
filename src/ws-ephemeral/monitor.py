"""
############################
# Author: Dhruvin Shah
# Date: 18th Sep 2023
############################

A worker that keep track of qBitTorrent connection
"""

import logging

import config
from lib.qbit import QbitManager

# Lets assume we have proper connection with the qBitTorrent
HEARTBEAT = True


def monitor() -> bool:
    """Monitor qBitTorrent instance is running as expected."""
    global HEARTBEAT
    try:
        QbitManager(
            host=config.QBIT_HOST,
            port=config.QBIT_PORT,
            username=config.QBIT_USERNAME,
            password=config.QBIT_PASSWORD,
        )
    except Exception:
        logging.error("Something wrong with Qbit, it's not accessible")
        HEARTBEAT = False
    else:
        logging.debug("Hearbeat detected")
        HEARTBEAT = True

    return HEARTBEAT
