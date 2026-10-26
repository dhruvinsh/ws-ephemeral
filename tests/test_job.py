import threading
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


def test_new_port_is_synced_to_gluetun(
    events: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ws_ephemeral.config import GluetunSettings

    gluetun_settings = GluetunSettings(
        url="http://gluetun:8000",
        api_key="test-secret",
        fixed_ports=(8080, 6881),
    )
    synced: list[tuple[int, GluetunSettings]] = []

    def fake_sync(port: int, settings: GluetunSettings) -> bool:
        synced.append((port, settings))
        return True

    monkeypatch.setattr(job, "sync_port", fake_sync)

    assert job.rotate_port(Settings(WS, QBIT, gluetun_settings)) == 4242
    assert synced == [(4242, gluetun_settings)]


def test_run_job_reports_gluetun_sync_failure(
    events: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ws_ephemeral.config import GluetunSettings

    gluetun_settings = GluetunSettings(
        url="http://gluetun:8000",
        api_key="test-secret",
        fixed_ports=(8080, 6881),
    )

    monkeypatch.setattr(job, "sync_port", lambda *_: False)

    assert job.run_job(Settings(WS, QBIT, gluetun_settings)) is False


def test_periodic_sync_waits_for_port_rotation_lock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ws_ephemeral.config import GluetunSettings

    settings = Settings(
        WS,
        QBIT,
        GluetunSettings(
            url="http://gluetun:8000",
            api_key="test-secret",
            fixed_ports=(8080, 6881),
        ),
    )
    lock_acquired = threading.Event()
    release_lock = threading.Event()
    sync_started = threading.Event()
    sync_called = threading.Event()

    def fake_sync(_: int, __: object) -> bool:
        sync_called.set()
        return True

    class FakeQbitForSync:
        def __init__(self, **_: object) -> None:
            self.client = type(
                "FakeClient",
                (),
                {
                    "application": type(
                        "FakeApplication",
                        (),
                        {"preferences": {"listen_port": 4242}},
                    )()
                },
            )()

    monkeypatch.setattr(job, "QbitManager", FakeQbitForSync)
    monkeypatch.setattr(job, "sync_port", fake_sync)

    def hold_lock() -> None:
        with job._gluetun_sync_lock:
            lock_acquired.set()
            release_lock.wait(timeout=2)

    holder = threading.Thread(target=hold_lock)
    holder.start()
    assert lock_acquired.wait(timeout=2)

    def run_sync() -> None:
        sync_started.set()
        job.sync_current_port(settings)

    syncer = threading.Thread(target=run_sync)
    syncer.start()
    assert sync_started.wait(timeout=2)

    # The sync must not run until the shared lock is released.
    assert not sync_called.is_set()
    release_lock.set()

    holder.join(timeout=2)
    syncer.join(timeout=2)

    assert not holder.is_alive()
    assert not syncer.is_alive()
    assert sync_called.is_set()


def test_new_port_does_not_sync_gluetun_when_unconfigured(
    events: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_sync(*_: object) -> bool:
        raise AssertionError("Gluetun should not be called")

    monkeypatch.setattr(job, "sync_port", unexpected_sync)

    assert job.rotate_port(Settings(WS, QBIT)) == 4242
