"""############################
# Author: Dhruvin Shah
# Date: 5th Sep 2022
############################

Windscribe module allow to setup the ephemeral port
"""

import re
from datetime import datetime, timedelta
from typing import Union

import httpx
from loguru import logger

from ws_ephemeral.cfg import config

from .cookie import default_cookie, load_cookie, save_cookie
from .decorators import login_required
from .types import Csrf


class Windscribe:
    """Windscribe api to enable ephemeral ports.

    Only works with non 2FA account (for now).
    """

    BASE_URL = "https://windscribe.com"
    CSRF_URL = "https://res.windscribe.com/res/logintoken"

    def __init__(self, username: str, password: str) -> None:
        headers = {
            "origin": self.BASE_URL,
            "referer": f"{self.BASE_URL}/login",
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/104.0.0.0 Safari/537.36"
            ),
        }

        self.is_authenticated = True
        cookie = load_cookie()
        if cookie is None:
            self.is_authenticated = False
            cookie = default_cookie()

        self.client = httpx.Client(headers=headers, cookies=cookie, timeout=config.REQUEST_TIMEOUT)

        # we will populate this later in the login call
        self.username = username
        self.password = password

    def __enter__(self) -> "Windscribe":
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Close httpx session"""
        self.close()

    @property
    def is_authenticated(self) -> bool:
        """If session is authenticated."""
        return self._is_authenticated

    @is_authenticated.setter
    def is_authenticated(self, value: bool) -> None:
        """Set authentication status."""
        self._is_authenticated = value

    def initialize_csrf(self) -> Csrf:
        """Windscribe make separate request to get the csrf token"""
        resp = self.client.post(self.CSRF_URL)
        data = resp.json()
        return Csrf(time=data["csrf_time"], token=data["csrf_token"])

    def login(self) -> None:
        """Login in to the webpage."""
        csrf: Csrf = self.initialize_csrf()
        data = {
            "login": 1,
            "upgrade": 0,
            "csrf_time": csrf.time,
            "csrf_token": csrf.token,
            "username": self.username,
            "password": self.password,
            "code": "",  # 2FA code
        }
        self.client.post(f"{self.BASE_URL}/login", data=data)

        # save the cookie for the future use.
        save_cookie(self.client.cookies)

        self.is_authenticated = True
        logger.debug("login successful")

    @login_required
    def get_csrf(self) -> Csrf:
        """After login windscribe issue new csrf token within javascript"""
        url = f"{self.BASE_URL}/myaccount"
        resp = self.client.get(url)
        csrf_time = re.search(r"csrf_time = (?P<ctime>\d+)", resp.text)
        if csrf_time is None:
            raise ValueError("Can not work further, csrf_time not found, exited.")

        csrf_token = re.search(r"csrf_token = \'(?P<ctoken>\w+)\'", resp.text)
        if csrf_token is None:
            raise ValueError("Can not work further, csrf_token not found, exited.")

        return Csrf(time=int(csrf_time.groupdict()["ctime"]), token=csrf_token.groupdict()["ctoken"])

    @login_required
    def delete_ephm_port(self, csrf: Csrf) -> dict[str, Union[bool, int]]:
        """Ensure we delete the ephemeral port setting if any available.

        :param csrf: need to pass the csrf time and token.
        """
        url = f"{self.BASE_URL}/staticips/deleteEphPort"
        data = {
            "ctime": csrf.time,
            "ctoken": csrf.token,
        }
        resp = self.client.post(url, data=data)
        res = resp.json()
        logger.debug(f"ephimeral port deleted: {res}")

        return res

    @login_required
    def set_matching_port(self, csrf: Csrf) -> int:
        """Setup matching ephemeral port on windscribe.

        :param csrf: need to pass the csrf time and token.
        """
        url = f"{self.BASE_URL}/staticips/postEphPort"
        data = {
            # keeping port empty makes it to request matching port
            "port": "",
            "ctime": csrf.time,
            "ctoken": csrf.token,
        }
        resp = self.client.post(url, data=data)
        res = resp.json()
        logger.debug(f"new ephimeral port set: {res}")

        if res["success"] != 1:
            raise ValueError("Not able to setup matching ephemeral port.")

        # lets make sure we actually had matching port
        external: int = res["epf"]["ext"]
        internal: int = res["epf"]["int"]

        if external != internal:
            raise ValueError("Port setup done but matching port not found.")

        return internal

    def get_ephm_port(self) -> int:
        """Get active ephemeral port"""
        return 1

    @login_required
    def get_remaining_time(self) -> str | None:
        """Get remaining time in in the renewal."""
        # window.epfExpires = 1710753741
        url = f"{self.BASE_URL}/staticips/load"
        resp = self.client.get(url)
        renewal_epoch_search = re.search(r"window.epfExpires = (\d+)", resp.content.decode())
        if renewal_epoch_search is None:
            return None
        renewal_epoch = int(renewal_epoch_search.group(1))

        remaining_time = datetime.fromtimestamp(renewal_epoch) + timedelta(days=7) - datetime.now()

        return str(remaining_time)

    def close(self) -> None:
        """Close httpx session."""
        logger.debug("closing session")
        self.client.close()
