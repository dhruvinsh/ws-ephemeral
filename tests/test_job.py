from dataclasses import replace
from pathlib import Path

import pytest

from ws_ephemeral import job
from ws_ephemeral.config import QbitSettings, Settings, WindscribeSettings
from ws_ephemeral.windscribe import WindscribeError

WS = WindscribeSettings(
    username="u",
    password="p",
    totp=None,
    cookie_file=Path("cookie.pkl"),
    timeout=5,
)
QBIT = QbitSettings(host="h", port=1, username="u", password="p", private_tracker=True)


class FakeQbit:
    down = False


@pytest.fixture
def events(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Replace Windscribe and qBittorrent, and record what happened in which order."""
    log: list[str] = []
    FakeQbit.down = False

    class Qbit:
        def __init__(self, **_: object) -> None:
            log.append("qbit connect")
            if FakeQbit.down:
                raise ConnectionError("qbit is down")

        def set_listen_port(self, port: int) -> bool:
            log.append(f"qbit port {port}")
            return True

        def setup_private_tracker(self) -> bool:
            log.append("qbit private tracker")
            return True

    class Windscribe:
        def __init__(self, **_: object) -> None:
            pass

        def __enter__(self) -> Windscribe:
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def setup(self) -> int:
            log.append("ws setup")
            return 4242

    monkeypatch.setattr(job, "QbitManager", Qbit)
    monkeypatch.setattr(job, "Windscribe", Windscribe)
    return log


def test_new_port_is_handed_to_qbit_after_windscribe(events: list[str]) -> None:
    assert job.rotate_port(Settings(WS, QBIT)) == 4242

    assert events == [
        "qbit connect",
        "ws setup",
        "qbit port 4242",
        "qbit private tracker",
    ]


def test_private_tracker_setup_is_optional(events: list[str]) -> None:
    job.rotate_port(Settings(WS, replace(QBIT, private_tracker=False)))

    assert "qbit private tracker" not in events


def test_windscribe_is_untouched_when_qbit_is_down(events: list[str]) -> None:
    FakeQbit.down = True

    with pytest.raises(ConnectionError):
        job.rotate_port(Settings(WS, QBIT))

    assert events == ["qbit connect"]


def test_port_is_still_rotated_without_qbit(events: list[str]) -> None:
    assert job.rotate_port(Settings(WS, None)) == 4242

    assert events == ["ws setup"]


def test_run_job_reports_success(events: list[str]) -> None:
    assert job.run_job(Settings(WS, QBIT)) is True


def test_run_job_reports_failure_instead_of_raising(events: list[str]) -> None:
    FakeQbit.down = True

    assert job.run_job(Settings(WS, QBIT)) is False


def test_run_job_reports_a_windscribe_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def rejected(_: Settings) -> int:
        raise WindscribeError(702, "nope")

    monkeypatch.setattr(job, "rotate_port", rejected)

    assert job.run_job(Settings(WS, None)) is False
