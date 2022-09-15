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
from logger import create_logger

logger = create_logger("ws")


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
    def __init__(self, logger: logging.Logger) -> None:
        headers = {
            "origin": config.BASE_URL,
            "referer": config.LOGIN_URL,
            # pylint: disable=line-too-long
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
        }
        self.client = httpx.Client(headers=headers, cookies=config.COOKIES)

        # we will populate this later in the login call
        self.csrf: Csrf = self._get_csrf()

        self.logger = logger

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

        self.logger.info("csrf renewed successfully.")
        return new_csrf

    def _login(self) -> None:
        """login in to the webpage"""
        data = {
            "login": 1,
            "upgrade": 0,
            "csrf_time": self.csrf["csrf_time"],
            "csrf_token": self.csrf["csrf_token"],
            "username": config.USERNAME,
            "password": config.PASSWORD,
            "code": "",
        }
        self.client.post(config.LOGIN_URL, data=data)
        self.logger.info("login successful")

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
        self.logger.info("ephimeral port deleted: %s", res)

        return res

    def _set_ephm_port(self) -> dict[str, Union[dict[str, Union[str, int]], int]]:
        data = {
            "port": config.PORT,
            "ctime": self.csrf["csrf_time"],
            "ctoken": self.csrf["csrf_token"],
        }
        resp = self.client.post(config.SET_EPHEM_URL, data=data)
        res = resp.json()
        self.logger.info("new ephimeral port set: %s", res)

        return res

    def setup(self) -> None:
        """perform ephemeral port setup here"""
        self._login()

        # after login we need to update the csrf token agian,
        # windscribe puts new csrf token in the javascript
        self.csrf = self._renew_csrf()

        self._delete_ephm_port()
        res = self._set_ephm_port()

        if res["success"] == 1:
            self.logger.info("Port renewed successfully.")
        else:
            self.logger.error("Port renewal failed, check config or open suport ticket")

    def close(self) -> None:
        """close httpx session"""
        self.logger.info("closing session")
        self.client.close()


def reset_ephemeral_port() -> None:
    """Main function responsible for resetting the ephemeral port.
    Steps:
    - login to windscribe
    - fetch new csrf token
    - go to my account
    - delete ephemeral ports (disregard existance of one or not)
    - set new ports
    - clean up the session
    """
    ws = Windscribe(logger=logger)
    ws.setup()
    ws.close()
