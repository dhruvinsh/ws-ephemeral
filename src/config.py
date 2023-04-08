"""
config module
"""
import logging
import os
import sys
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

BASE_PATH: Path = Path(".")

# common config
CSRF_URL: str = "https://res.windscribe.com/res/logintoken"

BASE_URL: str = "https://windscribe.com/"
LOGIN_URL: str = BASE_URL + "login"
MYACT_URL: str = BASE_URL + "myaccount"

STATICIP: str = BASE_URL + "staticips/"
EPHEM_URL: str = STATICIP + "load"
DEL_EPHEM_URL: str = STATICIP + "deleteEphPort"
SET_EPHEM_URL: str = STATICIP + "postEphPort"

# WS config
WS_USERNAME: str = os.getenv("WS_USERNAME", "")
WS_PASSWORD: str = os.getenv("WS_PASSWORD", "")

if not all([WS_USERNAME, WS_PASSWORD]):
    logger.error("ENV: WS_USERNAME and WS_PASSWORD need to be set")
    sys.exit(1)

# some HTML id for the login purpose
# TODO: expose via config file
USERNAME_ID: str = "username"
PASSWORD_ID: str = "password"

COOKIES = httpx.Cookies()
COOKIES.set("i_can_has_cookie", "1")
COOKIES.set("ref", "https://windscribe.com/")


# fmt: off
# some qbitconfig
QBIT_USERNAME: str = os.getenv("QBIT_USERNAME", "default123!!")
QBIT_PASSWORD: str = os.getenv("QBIT_PASSWORD", "default123!!")
QBIT_HOST: str     = os.getenv("QBIT_HOST", "127.0.0.1")
QBIT_PORT: int     = int(os.getenv("QBIT_PORT", "8080"))
# fmt: on

QBIT_FOUND = True
# if user is running latest build without qbit env then let them run but disable the
# qbit functions
if QBIT_USERNAME == "default123!!" or QBIT_PASSWORD == "default123!!":
    logger.warning("QBIT related setup not found, setup env as soon as possible")
    QBIT_FOUND = False

_QBIT_PRIVATE_TRACKER: str = os.getenv("QBIT_PRIVATE_TRACKER", "false")
QBIT_PRIVATE_TRACKER: bool = True if _QBIT_PRIVATE_TRACKER.lower() == "true" else False
