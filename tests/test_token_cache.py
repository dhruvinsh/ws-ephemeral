import os
import pickle
from pathlib import Path

import pytest

from ws_ephemeral.token_cache import SESSION_KEY, load_token, save_token


def test_token_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "cookie.pkl"

    save_token(path, "tok")

    assert load_token(path) == "tok"


def test_missing_file_means_no_token(tmp_path: Path) -> None:
    assert load_token(tmp_path / "nope.pkl") is None


def test_old_cookie_file_is_still_read(tmp_path: Path) -> None:
    # what the previous version saved: the whole cookie jar
    path = tmp_path / "cookie.pkl"
    path.write_bytes(
        pickle.dumps({"i_can_has_cookie": "1", "ref": "x", SESSION_KEY: "tok"})
    )

    assert load_token(path) == "tok"


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"not a pickle",
        pickle.dumps({}),
        pickle.dumps(["not", "a", "dict"]),
        pickle.dumps({SESSION_KEY: ""}),
        pickle.dumps({SESSION_KEY: 42}),
    ],
)
def test_unusable_cache_means_no_token(tmp_path: Path, content: bytes) -> None:
    path = tmp_path / "cookie.pkl"
    path.write_bytes(content)

    assert load_token(path) is None


def test_missing_directory_is_created(tmp_path: Path) -> None:
    path = tmp_path / "a" / "b" / "cookie.pkl"

    save_token(path, "tok")

    assert load_token(path) == "tok"


@pytest.mark.skipif(os.name != "posix", reason="needs unix permissions")
def test_cache_is_private_to_the_user(tmp_path: Path) -> None:
    path = tmp_path / "cookie.pkl"

    save_token(path, "tok")

    assert path.stat().st_mode & 0o777 == 0o600
