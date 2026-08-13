"""Windscribe module to setup ephemeral ports.

Windscribe's website is protected against automated logins, so authentication
goes through the desktop client api instead:

    AuthToken -> Session -> WebSession -> web session cookie

The resulting cookie is what the account pages expect, and is used to read the
csrf token and to manage the ephemeral port.
"""

import base64
import hashlib
import logging
import re
import time
from types import TracebackType
from typing import Any, TypedDict, final

import httpx
import pyotp

import config
from lib.decorators import login_required

from . import captcha
from .session import clear_session, load_session, update_session

# secret the desktop client uses to sign the auth token
_TOKEN_SECRET = "if_you_copy_this_you_might_die_a_painful_death"
_WEB_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
)
_API_UA = f"Windscribe/{config.WS_APP_VERSION} ({config.WS_PLATFORM})"
_SESSION_COOKIE = "ws_session_auth_hash"
# web sessions live for about an hour, refresh well before that
_COOKIE_TTL = 45 * 60
# a captcha solution can be off, but never hammer the login endpoint
_LOGIN_ATTEMPTS = 3
_LOGIN_RETRY_DELAY = 5


class Csrf(TypedDict):
    """CSRF type dict"""

    csrf_time: int
    csrf_token: str


class WindscribeError(Exception):
    """Raised when Windscribe rejects a request."""


def _decode_image(value: str) -> bytes:
    """Decode a base64 image coming from the api.

    Args:
        value (str): Base64 data, optionally as a data uri.

    Returns:
        bytes: The decoded image.
    """
    return base64.b64decode(re.sub(r"^data:image/\w+;base64,", "", value))


@final
class Windscribe:
    """Windscribe API to enable ephemeral ports.

    This class handles authentication, CSRF token management, and API requests
    to set or delete ephemeral ports.

    Attributes:
        client (httpx.Client): The HTTP client for making requests.
        csrf (Csrf | None): The CSRF token and time, once fetched.
        username (str): The username for authentication.
        password (str): The password for authentication.
        totp (str | None): The TOTP secret for 2FA, if available.
        logger (logging.Logger): Logger for the class.
    """

    # pylint: disable=redefined-outer-name
    def __init__(
        self,
        username: str,
        password: str,
        totp: str | None = None,
        auth_hash: str | None = None,
    ) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

        self.username = username
        self.password = password
        self.totp = totp

        self.client = httpx.Client(timeout=config.REQUEST_TIMEOUT)
        self.csrf: Csrf | None = None

        session = load_session()
        # a user supplied hash is never replaced on our own
        self._static_auth_hash = auth_hash is not None
        self._auth_hash = auth_hash or session.get("auth_hash")

        self._cookie = session.get("web_cookie")
        if self._cookie and session.get("web_cookie_expires", 0.0) < time.time():
            self.logger.debug("cached web session is stale")
            self._cookie = None

        self._is_authenticated = self._cookie is not None

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

    def _api_post(
        self, url: str, data: dict[str, str], auth: str = "0"
    ) -> dict[str, Any]:
        """Call the desktop client api.

        Args:
            url (str): The endpoint to call.
            data (dict[str, str]): The form payload.
            auth (str): The bearer token, "0" when not authenticated yet.

        Returns:
            dict[str, Any]: The payload's data section.

        Raises:
            WindscribeError: If the api reports an error.
        """
        headers = {
            "content-type": "text/html; charset=utf-8",
            "user-agent": _API_UA,
            "accept": "application/json, text/plain, */*",
            "authorization": f"Bearer {auth}",
        }
        resp = self.client.post(
            url, params=config.WS_API_PARAMS, headers=headers, data=data
        )

        try:
            payload: Any = resp.json()
        except ValueError as err:
            raise WindscribeError(
                f"{url} returned a non json response ({resp.status_code})"
            ) from err

        if not isinstance(payload, dict) or "data" not in payload:
            reason = "unknown error"
            if isinstance(payload, dict):
                reason = str(payload.get("errorMessage") or payload)
            raise WindscribeError(f"{url} failed ({resp.status_code}): {reason}")

        return payload["data"]

    def _web_headers(self) -> dict[str, str]:
        """Build the headers used on the account pages.

        Returns:
            dict[str, str]: Headers carrying the web session cookie.
        """
        headers = {"user-agent": _WEB_UA, "origin": config.BASE_URL}
        if self._cookie:
            headers["cookie"] = f"{_SESSION_COOKIE}={self._cookie};"
        return headers

    def _solve_captcha(self, challenge: dict[str, Any] | None) -> dict[str, str]:
        """Solve the slider captcha, if the api asked for one.

        Args:
            challenge (dict[str, Any] | None): The captcha section of the api response.

        Returns:
            dict[str, str]: The extra login fields, empty when there is no captcha.

        Raises:
            WindscribeError: If the captcha cannot be solved headlessly.
        """
        if not challenge:
            return {}

        if challenge.get("ascii_art"):
            raise WindscribeError(
                "Windscribe asked for an ascii captcha which cannot be solved "
                "automatically, set WS_AUTH_HASH instead."
            )

        background, slider = challenge.get("background"), challenge.get("slider")
        if not background or not slider:
            raise WindscribeError("Windscribe sent an unsupported captcha.")

        solution = captcha.solve(
            _decode_image(background), _decode_image(slider), int(challenge["top"])
        )
        self.logger.debug("captcha solved, offset %d", solution.solution)

        data = {"captcha_solution": str(solution.solution)}
        for idx, x in enumerate(solution.trail_x):
            data[f"captcha_trail[x][{idx}]"] = f"{x:.3f}"
        for idx, y in enumerate(solution.trail_y):
            data[f"captcha_trail[y][{idx}]"] = f"{y:.3f}"
        return data

    def _api_login(self) -> str:
        """Log into the api with username and password.

        Returns:
            str: The api session hash.

        Raises:
            WindscribeError: If the login keeps failing.
        """
        if not (self.username and self.password):
            raise WindscribeError(
                "WS_USERNAME and WS_PASSWORD are required when WS_AUTH_HASH is not set."
            )

        error = WindscribeError("login did not run")
        for attempt in range(1, _LOGIN_ATTEMPTS + 1):
            token = self._api_post(config.AUTH_TOKEN_URL, {"username": self.username})
            secure_token: str = token["token"]
            signature = hashlib.sha256(
                (secure_token + _TOKEN_SECRET).encode()
            ).hexdigest()

            data = {
                "username": self.username,
                "password": self.password,
                "session_type_id": "3",
                "secure_token": secure_token,
                "secure_token_sig": signature,
            }
            if self.totp:
                data["2fa_code"] = pyotp.TOTP(self.totp).now()
            data.update(self._solve_captcha(token.get("captcha")))

            try:
                session = self._api_post(config.SESSION_URL, data)
            except WindscribeError as err:
                error = err
                self.logger.warning("login attempt %d failed: %s", attempt, err)
                if attempt < _LOGIN_ATTEMPTS:
                    time.sleep(_LOGIN_RETRY_DELAY)
                continue

            auth_hash: str | None = session.get("session_auth_hash")
            if not auth_hash:
                raise WindscribeError("Windscribe did not return a session hash.")

            self.logger.info("logged into the windscribe api")
            return auth_hash

        raise error

    def _get_auth_hash(self, renew: bool = False) -> str:
        """Get the api session hash, logging in when needed.

        Args:
            renew (bool): Force a new login instead of reusing the cached hash.

        Returns:
            str: The api session hash.
        """
        if self._auth_hash and (self._static_auth_hash or not renew):
            return self._auth_hash

        self._auth_hash = self._api_login()
        update_session(auth_hash=self._auth_hash)
        return self._auth_hash

    def _create_web_session(self, auth_hash: str) -> None:
        """Exchange the api session for a website session cookie.

        Args:
            auth_hash (str): The api session hash.

        Raises:
            WindscribeError: If Windscribe does not hand out a session.
        """
        data = self._api_post(
            config.WEB_SESSION_URL,
            {"temp_session": "1", "session_type_id": "1"},
            auth=auth_hash,
        )
        temp_session: str | None = data.get("temp_session")
        if not temp_session:
            raise WindscribeError("Windscribe did not return a temporary web session.")

        # the redirect is what carries the cookie, so don't follow it
        resp = self.client.get(
            config.MYACT_URL,
            params={"temp_session": temp_session},
            headers={"user-agent": _WEB_UA},
            follow_redirects=False,
        )
        cookie = resp.cookies.get(_SESSION_COOKIE)
        if not cookie:
            raise WindscribeError(
                f"Windscribe did not hand out a web session ({resp.status_code})."
            )

        self._cookie = cookie
        update_session(web_cookie=cookie, web_cookie_expires=time.time() + _COOKIE_TTL)
        self.logger.debug("web session created")

    def _reset_web_session(self) -> None:
        """Forget the current web session."""
        self._cookie = None
        self.is_authenticated = False
        clear_session("web_cookie", "web_cookie_expires")

    def login(self) -> None:
        """Login to Windscribe.

        Creates a website session out of the api session hash, logging into the
        api first when there is no usable hash cached.
        """
        try:
            self._create_web_session(self._get_auth_hash())
        except WindscribeError as err:
            if self._static_auth_hash or not self.username:
                raise
            self.logger.warning("cached session was rejected (%s), logging in", err)
            self._create_web_session(self._get_auth_hash(renew=True))

        self.is_authenticated = True
        self.logger.debug("login successful")

    @login_required
    def renew_csrf(self, retry: bool = True) -> Csrf:
        """Renew CSRF token.

        Windscribe puts the CSRF token in the account page's JavaScript.

        Args:
            retry (bool): Rebuild the web session once if it is no longer valid.

        Returns:
            Csrf: The new CSRF token and time.

        Raises:
            WindscribeError: If the CSRF time or token is not found.
        """
        resp = self.client.get(
            config.MYACT_URL, headers=self._web_headers(), follow_redirects=False
        )

        csrf_time = re.search(r"csrf_time = (?P<ctime>\d+)", resp.text)
        csrf_token = re.search(r"csrf_token = \'(?P<ctoken>\w+)\'", resp.text)

        if csrf_time is None or csrf_token is None:
            if retry:
                self.logger.warning("account page did not load, renewing the session")
                self._reset_web_session()
                return self.renew_csrf(retry=False)
            raise WindscribeError(
                f"Can not work further, csrf not found ({resp.status_code}), exited."
            )

        new_csrf: Csrf = {
            "csrf_time": int(csrf_time.groupdict()["ctime"]),
            "csrf_token": csrf_token.groupdict()["ctoken"],
        }

        self.logger.debug("csrf renewed successfully.")
        return new_csrf

    def _csrf_data(self) -> dict[str, Any]:
        """Build the CSRF payload shared by the ephemeral port calls.

        Returns:
            dict[str, Any]: The CSRF form fields.
        """
        if self.csrf is None:
            self.csrf = self.renew_csrf()

        return {"ctime": self.csrf["csrf_time"], "ctoken": self.csrf["csrf_token"]}

    @login_required
    def delete_ephm_port(self) -> dict[str, bool | int]:
        """Delete ephemeral port.

        Ensures that any existing ephemeral port setting is deleted.

        Returns:
            dict[str, bool | int]: The response from the API.
        """
        resp = self.client.post(
            config.DEL_EPHEM_URL, data=self._csrf_data(), headers=self._web_headers()
        )
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
            WindscribeError: If unable to set up a matching ephemeral port or if the external and internal ports do not match.
        """
        # keeping port empty makes it to request matching port
        data = {"port": "", **self._csrf_data()}
        resp = self.client.post(
            config.SET_EPHEM_URL, data=data, headers=self._web_headers()
        )
        res = resp.json()
        self.logger.debug("new ephimeral port set: %s", res)

        if res.get("success") != 1:
            raise WindscribeError(
                f"Not able to setup matching ephemeral port: {res.get('message', res)}"
            )

        # lets make sure we actually had matching port
        external: int = res["epf"]["ext"]
        internal: int = res["epf"]["int"]

        if external != internal:
            raise WindscribeError("Port setup done but matching port not found.")

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
