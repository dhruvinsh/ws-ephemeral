"""Windscribe module to setup ephemeral ports.

This module provides the Windscribe class to interact with the Windscribe API,
allowing users to manage ephemeral ports and handle authentication.
"""

import logging
import re
from types import TracebackType
from typing import TypedDict, final

import httpx
import pyotp

import config
from lib.decorators import login_required

from .cookie import default_cookie, load_cookie, save_cookie


class Csrf(TypedDict):
    """CSRF type dict"""

    csrf_time: int
    csrf_token: str


@final
class Windscribe:
    """Windscribe API to enable ephemeral ports.

    This class handles authentication, CSRF token management, and API requests
    to set or delete ephemeral ports. Only works with non-2FA accounts (for now).

    Attributes:
        client (httpx.Client): The HTTP client for making requests.
        csrf (Csrf): The CSRF token and time.
        username (str): The username for authentication.
        password (str): The password for authentication.
        totp (str | None): The TOTP secret for 2FA, if available.
        logger (logging.Logger): Logger for the class.
    """

    # pylint: disable=redefined-outer-name
    def __init__(self, username: str, password: str, totp: str | None = None) -> None:
        headers = {
            "origin": config.BASE_URL,
            "referer": config.LOGIN_URL,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",  # ruff: noqa: E501
        }

        self._is_authenticated = True
        cookie = load_cookie()
        if cookie is None:
            self._is_authenticated = False
            cookie = default_cookie()

        self.client = httpx.Client(
            headers=headers, cookies=cookie, timeout=config.REQUEST_TIMEOUT
        )

        # we will populate this later in the login call
        self.csrf: Csrf = self.get_csrf()
        self.username = username
        self.password = password
        self.totp = totp

        self.logger = logging.getLogger(self.__class__.__name__)

    def __enter__(self) -> "Windscribe":
        """Context manager entry.

        Returns:
            Windscribe: The Windscribe instance.
        """
        return self

    def __exit__(
        self,
        exc_type: BaseException | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Context manager exit.

        Closes the HTTP client session.

        Args:
            exc_type (BaseException | None): The exception type, if any.
            exc_value (BaseException | None): The exception value, if any.
            traceback (TracebackType | None): The traceback, if any.
        """
        self.close()

    @property
    def is_authenticated(self) -> bool:
        """Check if session is authenticated.

        Returns:
            bool: True if authenticated, False otherwise.
        """
        return self._is_authenticated

    @is_authenticated.setter
    def is_authenticated(self, value: bool) -> None:
        """Set authentication status.

        Args:
            value (bool): The new authentication status.
        """
        self._is_authenticated = value

    def get_csrf(self) -> Csrf:
        """Get CSRF token.

        Makes a request to the Windscribe API to get the CSRF token.

        Returns:
            Csrf: The CSRF token and time.
        """
        resp = self.client.post(config.CSRF_URL)
        return resp.json()

    @login_required
    def renew_csrf(self) -> Csrf:
        """Renew CSRF token.

        After login, Windscribe issues a new CSRF token within JavaScript.

        Returns:
            Csrf: The new CSRF token and time.

        Raises:
            ValueError: If CSRF time or token is not found.
        """
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

    def login(self) -> None:
        """Login to the Windscribe webpage.

        Authenticates the user using the provided username, password, and TOTP code (if available).
        Updates the CSRF token and saves the session cookies for future use.
        """
        # NOTE: at the given moment try to resolve totp so that we don't have any delay.
        totp = ""
        if self.totp is not None:
            totp = pyotp.TOTP(self.totp).now()

        data = {
            "login": 1,
            "upgrade": 0,
            "csrf_time": self.csrf["csrf_time"],
            "csrf_token": self.csrf["csrf_token"],
            "username": self.username,
            "password": self.password,
            "code": totp,
        }
        _ = self.client.post(config.LOGIN_URL, data=data)

        # save the cookie for the future use.
        save_cookie(self.client.cookies)

        self.is_authenticated = True
        self.logger.debug("login successful")

    @login_required
    def delete_ephm_port(self) -> dict[str, bool | int]:
        """Delete ephemeral port.

        Ensures that any existing ephemeral port setting is deleted.

        Returns:
            dict[str, bool | int]: The response from the API.
        """
        data = {
            "ctime": self.csrf["csrf_time"],
            "ctoken": self.csrf["csrf_token"],
        }
        resp = self.client.post(config.DEL_EPHEM_URL, data=data)
        res = resp.json()
        self.logger.debug("ephimeral port deleted: %s", res)

        return res

    @login_required
    def set_matching_port(self) -> int:
        """Set matching ephemeral port.

        Sets up a matching ephemeral port on Windscribe.

        Returns:
            int: The matching ephemeral port.

        Raises:
            ValueError: If unable to set up a matching ephemeral port or if the external and internal ports do not match.
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
        """Perform ephemeral port setup.

        After login, updates the CSRF token, deletes any existing ephemeral port,
        and sets up a new matching ephemeral port.

        Returns:
            int: The new matching ephemeral port.
        """
        # after login we need to update the csrf token again,
        # windscribe puts new csrf token in the javascript
        self.csrf = self.renew_csrf()

        _ = self.delete_ephm_port()
        return self.set_matching_port()

    def close(self) -> None:
        """Close HTTP client session.

        Closes the HTTP client session and logs the action.
        """
        self.logger.debug("closing session")
        self.client.close()
