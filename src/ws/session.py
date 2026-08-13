"""Persist the Windscribe session between runs.

The api session hash is long lived, so it is cached to avoid logging in (and
solving a captcha) on every run. The web session cookie derived from it is
short lived and is cached only to skip a needless round trip.
"""

import json
import logging
from typing import Any, TypedDict

import config

logger = logging.getLogger(__name__)


class SessionData(TypedDict, total=False):
    """Cached Windscribe session state."""

    auth_hash: str
    web_cookie: str
    web_cookie_expires: float


def load_session() -> SessionData:
    """Read the cached session.

    Returns:
        SessionData: The cached session, empty when there is nothing usable.
    """
    if not config.WS_SESSION.exists():
        return SessionData()

    try:
        data: Any = json.loads(config.WS_SESSION.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        logger.warning("session cache is not readable, ignoring it")
        return SessionData()

    return data if isinstance(data, dict) else SessionData()


def save_session(session: SessionData) -> None:
    """Write the session cache.

    Args:
        session (SessionData): The session to store.
    """
    config.WS_SESSION.parent.mkdir(parents=True, exist_ok=True)
    config.WS_SESSION.write_text(json.dumps(session), encoding="utf-8")
    try:
        # the file holds credentials, keep it private
        config.WS_SESSION.chmod(0o600)
    except OSError:
        logger.debug("could not restrict permissions on the session cache")


def update_session(**fields: Any) -> None:
    """Merge the given fields into the session cache.

    Args:
        **fields (Any): The session fields to store.
    """
    session = load_session()
    session.update(fields)  # pyright: ignore[reportCallIssue]
    save_session(session)


def clear_session(*keys: str) -> None:
    """Drop the given fields from the session cache.

    Args:
        *keys (str): The session fields to remove.
    """
    session = load_session()
    for key in keys:
        _ = session.pop(key, None)  # pyright: ignore[reportArgumentType]
    save_session(session)
