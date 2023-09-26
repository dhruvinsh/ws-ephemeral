"""
############################
# Author: Dhruvin Shah
# Date: 5th Sep 2022
############################

Windscribe module allow to setup the ephemeral port
"""

import logging
import re
from typing import TypedDict, Union

import httpx

import config


class Csrf(TypedDict):
    """CSRF type dict"""

    csrf_time: int
    csrf_token: str


class Windscribe:
    """
    windscribe api to enable ephemeral ports.
    Only works with non 2FA account.
    """

    # pylint: disable=redefined-outer-name
    def __init__(self, username: str, password: str) -> None:
        headers = {
            "origin": config.BASE_URL,
            "referer": config.LOGIN_URL,
            # pylint: disable=line-too-long
            # ruff: noqa: E501
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
        }
        self.client = httpx.Client(headers=headers, cookies=config.COOKIES, timeout=config.REQUEST_TIMEOUT)

        # we will populate this later in the login call
        self.csrf: Csrf = self._get_csrf()
        self.username = username
        self.password = password

        self.logger = logging.getLogger(self.__class__.__name__)

    def __enter__(self) -> "Windscribe":
        """context manager entry"""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """close httpx session"""
        self.close()

    def _get_csrf(self) -> Csrf:
        """windscribe make seperate request to get the csrf token"""
        resp = self.client.post(config.CSRF_URL)
        return resp.json()

    def _renew_csrf(self) -> Csrf:
        """after login windscribe issue new csrf token withing javascript"""
        resp = self.client.get(config.MYACT_URL)
        csrf_time = re.search(r"csrf_time = (?P<ctime>\d+)", resp.text)
        if csrf_time is None:
            raise ValueError("Can not work further, csrf_time not found, exited.")

        csrf_token = re.search(r"csrf_token = \'(?P<ctoken>\w+)\'", resp.text)
        if csrf_token is None:
            raise ValueError("Can not work further, csrf_token not found, exited.")

        new_csrf: Csrf = {
            "csrf_time": int(csrf_time.groupdict()["ctime"]),
            "csrf_token": csrf_token.groupdict()["ctoken"],
        }

        self.logger.debug("csrf renewed successfully.")
        return new_csrf

    def _login(self) -> None:
        """login in to the webpage"""
        data = {
            "login": 1,
            "upgrade": 0,
            "csrf_time": self.csrf["csrf_time"],
            "csrf_token": self.csrf["csrf_token"],
            "username": self.username,
            "password": self.password,
            "code": "",
        }
        self.client.post(config.LOGIN_URL, data=data)
        self.logger.debug("login successful")

    def _delete_ephm_port(self) -> dict[str, Union[bool, int]]:
        """
        ensure we delete the ephemeral port setting if any available
        """
        data = {
            "ctime": self.csrf["csrf_time"],
            "ctoken": self.csrf["csrf_token"],
        }
        resp = self.client.post(config.DEL_EPHEM_URL, data=data)
        res = resp.json()
        self.logger.debug("ephimeral port deleted: %s", res)

        return res

    def _set_matching_port(self) -> int:
        """
        setup matching ephemeral port on WS
        """
        data = {
            # keeping port empty makes it to request matching port
            "port": "",
            "ctime": self.csrf["csrf_time"],
            "ctoken": self.csrf["csrf_token"],
        }
        resp = self.client.post(config.SET_EPHEM_URL, data=data)
        res = resp.json()
        self.logger.debug("new ephimeral port set: %s", res)

        if res["success"] != 1:
            raise ValueError("Not able to setup matching ephemeral port.")

        # lets make sure we actually had matching port
        external: int = res["epf"]["ext"]
        internal: int = res["epf"]["int"]

        if external != internal:
            raise ValueError("Port setup done but matching port not found.")

        return internal

    def setup(self) -> int:
        """perform ephemeral port setup here"""
        self._login()

        # after login we need to update the csrf token agian,
        # windscribe puts new csrf token in the javascript
        self.csrf = self._renew_csrf()

        self._delete_ephm_port()
        return self._set_matching_port()

    def close(self) -> None:
        """close httpx session"""
        self.logger.debug("closing session")
        self.client.close()
