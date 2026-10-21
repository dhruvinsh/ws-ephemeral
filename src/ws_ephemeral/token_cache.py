"""Cache of the Windscribe session token."""

import logging
import os
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)

# Windscribe's web session cookie, its value is the same session token that the
# API expects as `Authorization: Bearer <token>`. Keeping the same name/format as
# the previous cookie file means an already cached cookie keeps working.
SESSION_KEY = "ws_session_auth_hash"


def load_token(path: Path) -> str | None:
    """Load the cached session token.

    Args:
        path (Path): The cache file.

    Returns:
        str | None: The session token, or None if there is nothing usable cached.
    """
    if not path.exists():
        return None

    try:
        with open(path, "rb") as fp:
            data = pickle.load(fp)
    except Exception:
        # whatever is wrong with the cache, a fresh login fixes it
        logger.warning("ignoring unreadable session cache %s", path)
        return None

    token = data.get(SESSION_KEY) if isinstance(data, dict) else None
    return token if isinstance(token, str) and token else None


def save_token(path: Path, token: str) -> None:
    """Save the session token for the future use.

    The token is as good as a password, so the file is private to the user.

    Args:
        path (Path): The cache file.
        token (str): The session token returned by the Windscribe API.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # write next to the target and swap, so a crash never leaves a half written file
    tmp = path.with_name(path.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as fp:
        pickle.dump({SESSION_KEY: token}, fp)
    tmp.replace(path)
