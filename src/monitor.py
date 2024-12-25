"""
############################
# Author: Dhruvin Shah
# Date: 18th Sep 2023
############################

A worker that keeps track of qBitTorrent connection
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
        for qbit_port in config.QBIT_PORTS:
            QbitManager(
                host=config.QBIT_HOST,
                port=qbit_port,
                username=config.QBIT_USERNAME,
                password=config.QBIT_PASSWORD,
            )
    except Exception:
        logging.error("Something wrong with qBit, it's not accessible")
        HEARTBEAT = False
    else:
        logging.debug("Heartbeat detected")
        HEARTBEAT = True

    return HEARTBEAT

