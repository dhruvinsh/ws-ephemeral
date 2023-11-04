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
    """Load existing cookie."""
    if not config.COOKIE_PATH.exists():
        return None

    cookie = Cookies()
    with open(config.COOKIE_PATH, "rb") as ck:
        cookie_dict = pickle.load(ck)
        for k, v in cookie_dict.items():
            cookie.set(k, v)
        return cookie


def save_cookie(cookie: Cookies):
    """Save the cookie to the file for future use"""
    cookie_dict: dict[str, str] = {}
    for k, v in cookie.items():
        cookie_dict[k] = v

    with open(config.COOKIE_PATH, "wb") as ck:
        pickle.dump(cookie_dict, ck)
