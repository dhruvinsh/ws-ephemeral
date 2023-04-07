"""
Module that run the setup for windscrib's ephemeral port
"""
import logging
import time

from tqdm import trange

from logger import setup_logging
from util import to_seconds
from ws import reset_ephemeral_port

setup_logging()
logger = logging.getLogger(__name__)

# wait befor setting the ephemeral ports
DAYS: int = 7

while True:
    logger.info("setting the ephemeral port")
    reset_ephemeral_port()

    logger.info("going to wait patiently for %s days befor next reset", DAYS)
    for _ in trange(to_seconds(DAYS)):
        time.sleep(1)
