"""Windscribe endpoints and the settings collected by the command line."""

from dataclasses import dataclass, field
from pathlib import Path

BASE_URL: str = "https://windscribe.com/"
API_URL: str = "https://api.windscribe.com/"

AUTH_TOKEN_URL: str = API_URL + "AuthToken/login"
SESSION_URL: str = API_URL + "Session"
EPHEM_URL: str = API_URL + "EphPortForwarding"

COOKIE_FILE_NAME: str = "cookie.pkl"


# NOTE: secrets are excluded from repr so that they can never end up in a log line
@dataclass(frozen=True, slots=True)
class WindscribeSettings:
    """Everything needed to talk to Windscribe."""

    username: str
    password: str = field(repr=False)
    totp: str | None = field(repr=False)
    cookie_file: Path
    # None disables the timeout
    timeout: float | None


@dataclass(frozen=True, slots=True)
class QbitSettings:
    """Everything needed to talk to qBittorrent."""

    host: str
    port: int
    username: str
    password: str = field(repr=False)
    private_tracker: bool


@dataclass(frozen=True, slots=True)
class Settings:
    """All settings of a single run, `qbit` is None when qBittorrent isn't set up."""

    windscribe: WindscribeSettings
    qbit: QbitSettings | None
