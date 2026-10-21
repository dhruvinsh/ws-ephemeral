from pathlib import Path

import pytest
from typer.testing import CliRunner

from ws_ephemeral import cli
from ws_ephemeral.config import QbitSettings, Settings

runner = CliRunner()

CREDS = {"WS_USERNAME": "user", "WS_PASSWORD": "secret-pw"}


class Recorder:
    """Stands in for the job, the scheduler and the logging setup of the CLI."""

    def __init__(self) -> None:
        self.settings: list[Settings] = []
        self.debug: list[bool] = []
        self.served = False
        self.job_succeeds = True

    def run_job(self, settings: Settings) -> bool:
        self.settings.append(settings)
        return self.job_succeeds

    def setup_logging(self, debug: bool = False) -> None:
        self.debug.append(debug)

    def serve(self, _scheduler: object) -> None:
        self.served = True


@pytest.fixture
def rec(monkeypatch: pytest.MonkeyPatch) -> Recorder:
    """Nothing in these tests may touch the network or block on a scheduler."""
    recorder = Recorder()
    monkeypatch.setattr(cli, "run_job", recorder.run_job)
    monkeypatch.setattr(cli, "setup_logging", recorder.setup_logging)
    monkeypatch.setattr(cli, "serve", recorder.serve)
    return recorder


def test_help_needs_no_credentials(rec: Recorder) -> None:
    result = runner.invoke(cli.app, ["--help"])

    assert result.exit_code == 0
    assert "run" in result.output
    assert "daemon" in result.output


def test_command_help_needs_no_credentials(rec: Recorder) -> None:
    result = runner.invoke(cli.app, ["daemon", "--help"])

    assert result.exit_code == 0
    assert "--cron" in result.output


def test_version(rec: Recorder) -> None:
    result = runner.invoke(cli.app, ["--version"])

    assert result.exit_code == 0
    assert "ws-ephemeral" in result.output


def test_run_needs_credentials(rec: Recorder) -> None:
    result = runner.invoke(cli.app, ["run"])

    assert result.exit_code == 2
    assert rec.settings == []


def test_run_once(rec: Recorder) -> None:
    result = runner.invoke(cli.app, ["run"], env=CREDS)

    assert result.exit_code == 0
    [settings] = rec.settings
    assert settings.windscribe.username == "user"
    assert settings.windscribe.cookie_file.name == "cookie.pkl"
    assert settings.windscribe.timeout == 5
    assert settings.qbit is None


def test_run_fails_with_a_non_zero_exit_code(rec: Recorder) -> None:
    rec.job_succeeds = False

    result = runner.invoke(cli.app, ["run"], env=CREDS)

    assert result.exit_code == 1


def test_qbit_is_set_up_when_it_has_credentials(rec: Recorder) -> None:
    env = CREDS | {
        "QBIT_USERNAME": "admin",
        "QBIT_PASSWORD": "qbit-pw",
        "QBIT_HOST": "https://qbit.example.com",
        "QBIT_PORT": "443",
        "QBIT_PRIVATE_TRACKER": "true",
    }

    runner.invoke(cli.app, ["run"], env=env)

    [settings] = rec.settings
    assert settings.qbit == QbitSettings(
        host="https://qbit.example.com",
        port=443,
        username="admin",
        password="qbit-pw",
        private_tracker=True,
    )


def test_cookie_path_and_timeout_come_from_the_environment(rec: Recorder) -> None:
    env = CREDS | {"WS_COOKIE_PATH": "/data", "REQUEST_TIMEOUT": "-1"}

    runner.invoke(cli.app, ["run"], env=env)

    [settings] = rec.settings
    assert settings.windscribe.cookie_file == Path("/data/cookie.pkl")
    # -1 means no timeout
    assert settings.windscribe.timeout is None


def test_secrets_never_show_in_the_settings_repr(rec: Recorder) -> None:
    env = CREDS | {
        "WS_TOTP": "totp-secret",
        "QBIT_USERNAME": "admin",
        "QBIT_PASSWORD": "qbit-pw",
    }

    runner.invoke(cli.app, ["run"], env=env)

    [settings] = rec.settings
    assert settings.qbit is not None
    for secret in ("secret-pw", "totp-secret", "qbit-pw"):
        assert secret not in repr(settings)


@pytest.mark.parametrize(
    ("args", "env", "expected"),
    [
        ([], {}, False),
        (["--debug"], {}, True),
        ([], {"WS_DEBUG": "True"}, True),
        # the string "False" used to switch debug logging on
        ([], {"WS_DEBUG": "False"}, False),
    ],
)
def test_debug_logging(
    rec: Recorder, args: list[str], env: dict[str, str], expected: bool
) -> None:
    runner.invoke(cli.app, [*args, "run"], env=CREDS | env)

    assert rec.debug == [expected]


def test_daemon_serves_a_scheduler(rec: Recorder) -> None:
    result = runner.invoke(
        cli.app, ["daemon", "--days", "3", "--time", "04:15"], env=CREDS
    )

    assert result.exit_code == 0
    assert rec.served
    # the job itself only runs once the scheduler is started
    assert rec.settings == []


def test_oneshot_runs_once_without_a_scheduler(rec: Recorder) -> None:
    result = runner.invoke(cli.app, ["daemon"], env=CREDS | {"ONESHOT": "true"})

    assert result.exit_code == 0
    assert len(rec.settings) == 1
    assert not rec.served


def test_oneshot_failure_exits_non_zero(rec: Recorder) -> None:
    rec.job_succeeds = False

    result = runner.invoke(cli.app, ["daemon", "--oneshot"], env=CREDS)

    assert result.exit_code == 1
    assert not rec.served


@pytest.mark.parametrize(
    "args",
    [["--time", "25:00"], ["--days", "0"], ["--cron", "not a cron"]],
)
def test_daemon_rejects_bad_schedules(rec: Recorder, args: list[str]) -> None:
    result = runner.invoke(cli.app, ["daemon", *args], env=CREDS)

    assert result.exit_code == 2
    assert not rec.served
