"""Windscribe module to setup ephemeral ports.

This module provides the Windscribe class to interact with the Windscribe API,
allowing users to manage ephemeral ports and handle authentication.
"""

import logging
from types import TracebackType
from typing import Any, final

import httpx
import pyotp

import config
from lib.decorators import login_required

from .cookie import load_token, save_token

# error codes returned by the API when the session token is missing/rejected
_SESSION_ERROR_CODES = {500, 701}


class WindscribeError(Exception):
    """Error reported by the Windscribe API."""

    def __init__(self, code: int | None, message: str) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


@final
class Windscribe:
    """Windscribe API to enable ephemeral ports.

    This class handles authentication and API requests to set or delete ephemeral
    ports. Login is a two step process against the API, which results in a session
    token that is cached and sent as a bearer token on every other request.

    Attributes:
        client (httpx.Client): The HTTP client for making requests.
        token (str | None): The session token, if available.
        username (str): The username for authentication.
        password (str): The password for authentication.
        totp (str | None): The TOTP secret for 2FA, if available.
        logger (logging.Logger): Logger for the class.
    """

    # pylint: disable=redefined-outer-name
    def __init__(self, username: str, password: str, totp: str | None = None) -> None:
        headers = {
            "origin": config.BASE_URL.rstrip("/"),
            "referer": config.BASE_URL,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",  # ruff: noqa: E501
        }

        self.token: str | None = load_token()
        self._is_authenticated = self.token is not None

        self.client = httpx.Client(headers=headers, timeout=config.REQUEST_TIMEOUT)
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

    @staticmethod
    def _data(resp: httpx.Response) -> dict[str, Any]:
        """Unwrap the API response.

        Args:
            resp (httpx.Response): The response from the API.

        Returns:
            dict[str, Any]: The `data` part of the response.

        Raises:
            WindscribeError: If the API reported an error.
        """
        try:
            body = resp.json()
        except ValueError as exc:
            raise WindscribeError(
                None, f"unexpected response (HTTP {resp.status_code})"
            ) from exc

        if "errorCode" in body:
            raise WindscribeError(
                body["errorCode"], body.get("errorDescription") or body["errorMessage"]
            )

        return body["data"]

    def _request(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        """Make an authenticated API request.

        If the API rejects the session token (expired or revoked), login again once and
        retry the request.

        Args:
            method (str): The HTTP method.
            url (str): The API url.
            **kwargs: Passed to the httpx request, `data` gets the session token added.

        Returns:
            dict[str, Any]: The `data` part of the response.
        """
        for attempt in (1, 2):
            headers = {"authorization": f"Bearer {self.token or 'anonymous'}"}
            if method != "GET":
                kwargs["data"] = {
                    "session_auth_hash": self.token,
                    **kwargs.get("data", {}),
                }
            resp = self.client.request(method, url, headers=headers, **kwargs)

            try:
                return self._data(resp)
            except WindscribeError as exc:
                if exc.code not in _SESSION_ERROR_CODES or attempt == 2:
                    raise

                self.logger.warning("session rejected (%s), logging in again", exc)
                self.login()

        raise AssertionError("unreachable")

    def login(self) -> None:
        """Login to Windscribe.

        Fetches a one time login token and exchanges it, together with the credentials
        and TOTP code (if available), for a session token. The session token is saved
        for the future use.
        """
        resp = self.client.post(
            config.AUTH_TOKEN_URL,
            json={"username": self.username, "password": self.password},
            headers={"authorization": "Bearer anonymous"},
        )
        auth = self._data(resp)

        payload: dict[str, Any] = {
            "username": self.username,
            "password": self.password,
            "session_type_id": 1,
            "platform": "legacy-web",
            "secure_token": auth["token"],
            "secure_token_sig": auth["token_sig"],
        }
        # NOTE: resolve totp at the given moment so that we don't have any delay.
        if self.totp is not None:
            payload["2fa_code"] = pyotp.TOTP(self.totp).now()

        resp = self.client.post(
            config.SESSION_URL,
            json=payload,
            headers={"authorization": "Bearer anonymous"},
        )
        session = self._data(resp)

        self.token = session["session_auth_hash"]
        save_token(self.token)

        self.is_authenticated = True
        self.logger.debug("login successful")

    @login_required
    def get_ephm_port(self) -> int | None:
        """Get the current ephemeral port.

        Returns:
            int | None: The external port, or None if no ephemeral port is set.
        """
        epf = self._request("GET", config.EPHEM_URL)["epf"]
        self.logger.debug("current ephemeral port: %s", epf)

        if not epf:
            return None

        return int(epf["ext"])

    @login_required
    def delete_ephm_port(self, port: int) -> None:
        """Delete ephemeral port.

        Args:
            port (int): The external port to delete.
        """
        res = self._request("DELETE", config.EPHEM_URL, data={"id": port})
        self.logger.debug("ephemeral port deleted: %s", res)

    @login_required
    def set_matching_port(self) -> int:
        """Set matching ephemeral port.

        Sets up a matching ephemeral port on Windscribe.

        Returns:
            int: The matching ephemeral port.

        Raises:
            ValueError: If unable to set up a matching ephemeral port or if the external and internal ports do not match.
        """
        # not asking for a specific port makes it request matching port
        res = self._request("POST", config.EPHEM_URL)
        self.logger.debug("new ephemeral port set: %s", res)

        if res["success"] != 1:
            raise ValueError("Not able to setup matching ephemeral port.")

        # lets make sure we actually had matching port
        external = int(res["epf"]["ext"])
        internal = int(res["epf"]["int"])

        if external != internal:
            raise ValueError("Port setup done but matching port not found.")

        return internal

    def setup(self) -> int:
        """Perform ephemeral port setup.

        Deletes any existing ephemeral port, and sets up a new matching ephemeral port.

        Returns:
            int: The new matching ephemeral port.
        """
        current = self.get_ephm_port()
        if current is not None:
            self.delete_ephm_port(current)

        return self.set_matching_port()

    def close(self) -> None:
        """Close HTTP client session.

        Closes the HTTP client session and logs the action.
        """
        self.logger.debug("closing session")
        self.client.close()
