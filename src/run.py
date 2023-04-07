"""
Module that run the setup for windscrib's ephemeral port
"""
import time

from tqdm import trange

from logger import create_logger
from util import to_seconds
from ws import reset_ephemeral_port

# wait befor setting the ephemeral ports
DAYS: int = 7

logger = create_logger("run")

while True:
    logger.info("setting the ephemeral port")
    reset_ephemeral_port()

    logger.info("going to wait patiently for %s days befor next reset", DAYS)
    for _ in trange(to_seconds(DAYS)):
        time.sleep(1)
