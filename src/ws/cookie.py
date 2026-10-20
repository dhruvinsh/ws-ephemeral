import pickle

import config

# Windscribe's web session cookie, its value is the same session token that the
# API expects as `Authorization: Bearer <token>`. Keeping the same name/format as
# the previous cookie file means an already cached cookie keeps working.
SESSION_KEY = "ws_session_auth_hash"


def load_token() -> str | None:
    """Load the cached session token.

    Reads the pickle file and looks for the session token.

    Returns:
        str | None: The session token, or None if there is nothing cached.
    """
    if not config.WS_COOKIE.exists():
        return None

    try:
        with open(config.WS_COOKIE, "rb") as ck:
            cookie_dict = pickle.load(ck)
    except (pickle.UnpicklingError, EOFError):
        return None

    if not isinstance(cookie_dict, dict):
        return None

    return cookie_dict.get(SESSION_KEY) or None


def save_token(token: str) -> None:
    """Save the session token to a file for future use.

    Args:
        token (str): The session token returned by the Windscribe API.
    """
    config.WS_COOKIE.parent.mkdir(parents=True, exist_ok=True)
    with open(config.WS_COOKIE, "wb") as ck:
        pickle.dump({SESSION_KEY: token}, ck)
