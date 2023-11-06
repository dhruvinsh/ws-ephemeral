import pickle

from httpx import Cookies

import config


def default_cookie() -> Cookies:
    """Build default cookie."""
    cookie = Cookies()
    cookie.set("i_can_has_cookie", "1")
    cookie.set("ref", "https://windscribe.com/")
    return cookie


def load_cookie() -> None | Cookies:
    """Load existing cookie.

    Read the pickle back and create the cookie object for httpx.
    """
    if not config.WS_COOKIE.exists():
        return None

    cookie = Cookies()
    with open(config.WS_COOKIE, "rb") as ck:
        cookie_dict = pickle.load(ck)
        for k, v in cookie_dict.items():
            cookie.set(k, v)

    return cookie


def save_cookie(cookie: Cookies) -> None:
    """Save the cookie to the file for future use.

    Read the cookie data and convert to regular dictinary object so that it can be
    pickled to a file.

    :param cookie: a cookie object from httpx requests.
    """
    cookie_dict: dict[str, str] = {}
    for k, v in cookie.items():
        cookie_dict[k] = v

    with open(config.WS_COOKIE, "wb") as ck:
        pickle.dump(cookie_dict, ck)
