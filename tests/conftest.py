import pytest

# Everything the command line reads from the environment. A developer shell often has
# these set (direnv), which must never change what a test does.
ENV_VARS = [
    "WS_USERNAME",
    "WS_PASSWORD",
    "WS_TOTP",
    "WS_DEBUG",
    "WS_COOKIE_PATH",
    "QBIT_USERNAME",
    "QBIT_PASSWORD",
    "QBIT_HOST",
    "QBIT_PORT",
    "QBIT_PRIVATE_TRACKER",
    "REQUEST_TIMEOUT",
    "DAYS",
    "TIME",
    "CRON",
    "RUN_ON_START",
    "ONESHOT",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)
