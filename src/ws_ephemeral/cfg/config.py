"""Config module."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from loguru import logger

BASE_PATH = Path()
DEBUG = os.environ.get("WS_DEBUG") is not None

# only run once
# allows wg-ephemeral to be used as a cronjob
_ONESHOT = os.getenv("ONESHOT", "false")
ONESHOT = _ONESHOT.lower() == "true"

# https://www.python-httpx.org/advanced/#timeout-configuration
_REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "5"))
# timeouts are disabled if None is used
REQUEST_TIMEOUT = None if _REQUEST_TIMEOUT == -1 else _REQUEST_TIMEOUT


# WS config
WS_USERNAME = os.getenv("WS_USERNAME", "")
WS_PASSWORD = os.getenv("WS_PASSWORD", "")
WS_COOKIE = Path(os.getenv("WS_COOKIE_PATH", ".")) / "cookie.pkl"

if not all([WS_USERNAME, WS_PASSWORD]):
    logger.error("ENV: WS_USERNAME and WS_PASSWORD need to be set")
    sys.exit(1)

# some HTML id for the login purpose
# TODO: expose via config file
USERNAME_ID = "username"
PASSWORD_ID = "password"


# some qbit config
QBIT_USERNAME = os.getenv("QBIT_USERNAME")
QBIT_PASSWORD = os.getenv("QBIT_PASSWORD")
QBIT_HOST = os.getenv("QBIT_HOST", "127.0.0.1")
QBIT_PORT = int(os.getenv("QBIT_PORT", "8080"))

# if user is running latest build without qbit env then let them run but disable the
# qbit functions
QBIT_FOUND = True
if QBIT_USERNAME is None or QBIT_PASSWORD is None:
    logger.error("QBIT related setup not found, setup env as soon as possible")
    QBIT_FOUND = False

_QBIT_PRIVATE_TRACKER = os.getenv("QBIT_PRIVATE_TRACKER", "false")
QBIT_PRIVATE_TRACKER = _QBIT_PRIVATE_TRACKER.lower() == "true"

# wait before setting the ephemeral ports
_DAYS = os.getenv("DAYS", "6")
DAYS = int(_DAYS)
TIME = os.getenv("TIME", "02:00")
