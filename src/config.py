"""
config module
"""

import os
import sys
from pathlib import Path

# only run once
# allows wg-ephemeral to be used as a cronjob
_ONESHOT: str = os.getenv("ONESHOT", "false")
ONESHOT: bool = True if _ONESHOT.lower() == "true" else False

# https://www.python-httpx.org/advanced/#timeout-configuration
_REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "5"))
# timeouts are disabled if None is used
REQUEST_TIMEOUT: int | None = None if _REQUEST_TIMEOUT == -1 else _REQUEST_TIMEOUT

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
WS_TOTP: str | None = os.getenv("WS_TOTP", None)
WS_COOKIE = Path(os.getenv("WS_COOKIE_PATH", ".")) / "cookie.pkl"

if not all([WS_USERNAME, WS_PASSWORD]):
    print("ENV: WS_USERNAME and WS_PASSWORD need to be set")
    sys.exit(1)

# some HTML id for the login purpose
# TODO: expose via config file
USERNAME_ID: str = "username"
PASSWORD_ID: str = "password"


# fmt: off
# some qbit config
QBIT_USERNAME: str | None = os.getenv("QBIT_USERNAME") or None
QBIT_PASSWORD: str | None = os.getenv("QBIT_PASSWORD") or None
QBIT_API_KEY: str | None  = os.getenv("QBIT_API_KEY") or None
QBIT_HOST: str            = os.getenv("QBIT_HOST", "127.0.0.1")
QBIT_PORT: int            = int(os.getenv("QBIT_PORT", "8080"))
# fmt: on

if QBIT_API_KEY and (QBIT_USERNAME or QBIT_PASSWORD):
    print("ENV: use either QBIT_API_KEY or qBittorrent username/password")
    sys.exit(1)

if not QBIT_API_KEY and bool(QBIT_USERNAME) != bool(QBIT_PASSWORD):
    print("ENV: QBIT_USERNAME and QBIT_PASSWORD must be set together")
    sys.exit(1)

qbit_found = bool(QBIT_API_KEY or (QBIT_USERNAME and QBIT_PASSWORD))
if not qbit_found:
    print("QBIT related setup not found, setup env as soon as possible")

_QBIT_PRIVATE_TRACKER: str = os.getenv("QBIT_PRIVATE_TRACKER", "false")
QBIT_PRIVATE_TRACKER: bool = True if _QBIT_PRIVATE_TRACKER.lower() == "true" else False


# Gluetun control server config. Setting GLUETUN_URL enables port synchronization.
GLUETUN_URL: str | None = os.getenv("GLUETUN_URL") or None
GLUETUN_API_KEY: str | None = os.getenv("GLUETUN_API_KEY") or None
GLUETUN_USERNAME: str | None = os.getenv("GLUETUN_USERNAME") or None
GLUETUN_PASSWORD: str | None = os.getenv("GLUETUN_PASSWORD") or None

if GLUETUN_URL and bool(GLUETUN_USERNAME) != bool(GLUETUN_PASSWORD):
    print("ENV: GLUETUN_USERNAME and GLUETUN_PASSWORD must be set together")
    sys.exit(1)

if GLUETUN_URL and GLUETUN_API_KEY and GLUETUN_USERNAME:
    print("ENV: use either GLUETUN_API_KEY or Gluetun username/password")
    sys.exit(1)


# wait before setting the ephemeral ports
try:
    DAYS: int = int(os.getenv("DAYS", 6))
except TypeError:
    print("DAYS must be integer")
TIME: str = os.getenv("TIME", "02:00")
