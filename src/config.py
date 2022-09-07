"""
config module
"""
import os
import sys
from typing import Optional

import httpx

from logger import create_logger
from util import validate_port

logger = create_logger("config")

# common config
CSRF_URL: str = "https://res.windscribe.com/res/logintoken"

BASE_URL: str = "https://windscribe.com/"
LOGIN_URL: str = BASE_URL + "login"
MYACT_URL: str = BASE_URL + "myaccount"

STATICIP: str = BASE_URL + "staticips/"
EPHEM_URL: str = STATICIP + "load"
DEL_EPHEM_URL: str = STATICIP + "deleteEphPort"
SET_EPHEM_URL: str = STATICIP + "postEphPort"

USERNAME: Optional[str] = os.environ.get("WS_USERNAME")
PASSWORD: Optional[str] = os.environ.get("WS_PASSWORD")
PORT: int = validate_port(os.environ.get("WS_EPHEMERAL_PORT"))

if not all([USERNAME, PASSWORD]):
    logger.error("Environment variables: Username and Password need to be set")
    sys.exit(1)

# some HTML id for the login purpose
# TODO: expose via config file
USERNAME_ID: str = "username"
PASSWORD_ID: str = "password"

COOKIES = httpx.Cookies()
COOKIES.set("i_can_has_cookie", "1")
COOKIES.set("ref", "https://windscribe.com/")
