import json
import logging
import pickle
from pathlib import Path
from urllib.parse import parse_qs

import pytest
from fake_api import GOOD_TOKEN, FakeApi

from ws_ephemeral.token_cache import SESSION_KEY, load_token
from ws_ephemeral.windscribe import Windscribe, WindscribeError

AUTH = ("POST", "/AuthToken/login")
SESSION = ("POST", "/Session")
GET_PORT = ("GET", "/EphPortForwarding")
SET_PORT = ("POST", "/EphPortForwarding")


def make_ws(
    api: FakeApi,
    tmp_path: Path,
    *,
    totp: str | None = None,
    cookie_file: Path | None = None,
) -> Windscribe:
    return Windscribe(
        "user",
        "password1",
        totp,
        cookie_file=cookie_file or tmp_path / "cookie.pkl",
        client=api.client(),
    )


def test_setup_logs_in_and_caches_the_token(tmp_path: Path) -> None:
    api = FakeApi()

    assert make_ws(api, tmp_path).setup() == 7

    # there is no port yet, so there is nothing to delete
    assert api.calls() == [AUTH, SESSION, GET_PORT, SET_PORT]
    assert load_token(tmp_path / "cookie.pkl") == GOOD_TOKEN


def test_setup_replaces_an_existing_port(tmp_path: Path) -> None:
    api = FakeApi(port="5")

    assert make_ws(api, tmp_path).setup() == 7

    delete = next(r for r in api.requests if r.method == "DELETE")
    form = parse_qs(delete.content.decode())
    assert form["id"] == ["5"]
    assert form["session_auth_hash"] == [GOOD_TOKEN]
    # the port is deleted before the new one is requested
    assert api.calls()[-2:] == [("DELETE", "/EphPortForwarding"), SET_PORT]


def test_cached_token_is_used_without_logging_in(tmp_path: Path) -> None:
    (tmp_path / "cookie.pkl").write_bytes(pickle.dumps({SESSION_KEY: GOOD_TOKEN}))
    api = FakeApi()

    make_ws(api, tmp_path).setup()

    assert AUTH not in api.calls()
    assert api.requests[0].headers["authorization"] == f"Bearer {GOOD_TOKEN}"


def test_stale_cached_token_logs_in_again_and_is_replaced(tmp_path: Path) -> None:
    cookie = tmp_path / "cookie.pkl"
    cookie.write_bytes(pickle.dumps({SESSION_KEY: "stale"}))
    api = FakeApi()

    assert make_ws(api, tmp_path).setup() == 7

    assert api.calls()[:4] == [GET_PORT, AUTH, SESSION, GET_PORT]
    assert load_token(cookie) == GOOD_TOKEN


def test_totp_code_is_sent_when_there_is_a_secret(tmp_path: Path) -> None:
    api = FakeApi()

    make_ws(api, tmp_path, totp="JBSWY3DPEHPK3PXP").login()

    session = next(r for r in api.requests if r.url.path == "/Session")
    code = json.loads(session.content)["2fa_code"]
    assert len(code) == 6
    assert code.isdigit()


def test_no_totp_code_is_sent_without_a_secret(tmp_path: Path) -> None:
    api = FakeApi()

    make_ws(api, tmp_path).login()

    session = next(r for r in api.requests if r.url.path == "/Session")
    assert "2fa_code" not in json.loads(session.content)


def test_rejected_login_explains_how_to_fix_it(tmp_path: Path) -> None:
    api = FakeApi(
        session_error={
            "errorCode": 702,
            "errorMessage": "Could not log in",
            "errorDescription": "Could not log in with provided credentials",
        }
    )

    with pytest.raises(WindscribeError) as excinfo:
        make_ws(api, tmp_path).login()

    assert excinfo.value.code == 702
    assert "WS_PASSWORD" in str(excinfo.value)
    assert load_token(tmp_path / "cookie.pkl") is None


def test_unwritable_cache_does_not_stop_the_run(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # a file where the directory should be, so that the cache can never be written
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory")
    api = FakeApi()

    with caplog.at_level(logging.WARNING):
        port = make_ws(api, tmp_path, cookie_file=blocker / "cookie.pkl").setup()

    assert port == 7
    assert "could not save session token" in caplog.text


def test_mismatched_ports_are_rejected(tmp_path: Path) -> None:
    api = FakeApi(new_port=(7, 8))

    with pytest.raises(ValueError, match="matching port not found"):
        make_ws(api, tmp_path).setup()
