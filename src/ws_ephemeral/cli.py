"""Command line interface.

Every setting can be given as an option or as an environment variable, the
environment variables are the same as they always were.
"""

import functools
import logging
from dataclasses import dataclass, field
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Annotated

import typer

from .config import COOKIE_FILE_NAME, QbitSettings, Settings, WindscribeSettings
from .job import run_job
from .log import setup_logging
from .scheduler import build_scheduler, serve

logger = logging.getLogger(__name__)

app = typer.Typer(
    help="Keep a Windscribe ephemeral port forward, and qBittorrent, up to date.",
    no_args_is_help=True,
    add_completion=False,
    # a crash would otherwise print the local variables, passwords included
    pretty_exceptions_show_locals=False,
)


@dataclass(frozen=True, slots=True)
class _Options:
    """The options shared by every command, as given on the command line."""

    ws_username: str | None
    ws_password: str | None = field(repr=False)
    ws_totp: str | None = field(repr=False)
    cookie_path: Path
    request_timeout: int
    qbit_host: str
    qbit_port: int
    qbit_username: str | None
    qbit_password: str | None = field(repr=False)
    qbit_private_tracker: bool


def _show_version(value: bool) -> None:
    if value:
        typer.echo(f"ws-ephemeral {package_version('ws-ephemeral')}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    ws_username: Annotated[
        str | None, typer.Option(envvar="WS_USERNAME", help="Windscribe username.")
    ] = None,
    ws_password: Annotated[
        str | None, typer.Option(envvar="WS_PASSWORD", help="Windscribe password.")
    ] = None,
    ws_totp: Annotated[
        str | None,
        typer.Option(
            envvar="WS_TOTP",
            help="Windscribe 2FA secret (the base32 key, not a one time code).",
        ),
    ] = None,
    cookie_path: Annotated[
        Path,
        typer.Option(
            envvar="WS_COOKIE_PATH",
            help="Directory that keeps the session between runs, mount it as a "
            "volume in Docker.",
        ),
    ] = Path("."),
    request_timeout: Annotated[
        int,
        typer.Option(
            envvar="REQUEST_TIMEOUT",
            help="HTTP timeout in seconds, -1 disables it.",
        ),
    ] = 5,
    qbit_host: Annotated[
        str,
        typer.Option(
            envvar="QBIT_HOST",
            help="qBittorrent web address, like https://qbit.xyz.com or "
            "http://192.168.1.10.",
        ),
    ] = "127.0.0.1",
    qbit_port: Annotated[
        int, typer.Option(envvar="QBIT_PORT", help="qBittorrent web port.")
    ] = 8080,
    qbit_username: Annotated[
        str | None, typer.Option(envvar="QBIT_USERNAME", help="qBittorrent username.")
    ] = None,
    qbit_password: Annotated[
        str | None, typer.Option(envvar="QBIT_PASSWORD", help="qBittorrent password.")
    ] = None,
    qbit_private_tracker: Annotated[
        bool,
        typer.Option(
            "--qbit-private-tracker/--no-qbit-private-tracker",
            envvar="QBIT_PRIVATE_TRACKER",
            help="Get qBittorrent ready for private trackers by disabling dht, pex "
            "and lsd.",
        ),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option("--debug/--no-debug", envvar="WS_DEBUG", help="Debug logging."),
    ] = False,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_show_version,
            is_eager=True,
            help="Show the version and exit.",
        ),
    ] = False,
) -> None:
    """Options shared by all the commands.

    Prefer the environment variables over the options for the passwords, options
    are visible to every user of the machine in the process list.
    """
    setup_logging(debug)
    ctx.obj = _Options(
        ws_username=ws_username,
        ws_password=ws_password,
        ws_totp=ws_totp,
        cookie_path=cookie_path,
        request_timeout=request_timeout,
        qbit_host=qbit_host,
        qbit_port=qbit_port,
        qbit_username=qbit_username,
        qbit_password=qbit_password,
        qbit_private_tracker=qbit_private_tracker,
    )


def _settings(ctx: typer.Context) -> Settings:
    """Turn the shared options into settings.

    This is done by the commands, and not by the callback, so that `--help` works
    without having any credentials.
    """
    opts: _Options = ctx.obj
    if not opts.ws_username or not opts.ws_password:
        raise typer.BadParameter("WS_USERNAME and WS_PASSWORD need to be set")

    # qbit is optional, the port is still rotated without it
    qbit = None
    if opts.qbit_username and opts.qbit_password:
        qbit = QbitSettings(
            host=opts.qbit_host,
            port=opts.qbit_port,
            username=opts.qbit_username,
            password=opts.qbit_password,
            private_tracker=opts.qbit_private_tracker,
        )

    return Settings(
        windscribe=WindscribeSettings(
            username=opts.ws_username,
            password=opts.ws_password,
            totp=opts.ws_totp,
            cookie_file=opts.cookie_path / COOKIE_FILE_NAME,
            timeout=None if opts.request_timeout == -1 else opts.request_timeout,
        ),
        qbit=qbit,
    )


@app.command()
def run(ctx: typer.Context) -> None:
    """Rotate the ephemeral port once and exit.

    Meant for an external scheduler like cron or a systemd timer, the exit code is 1
    if anything failed.
    """
    if not run_job(_settings(ctx)):
        raise typer.Exit(code=1)


@app.command()
def daemon(
    ctx: typer.Context,
    days: Annotated[
        int, typer.Option(envvar="DAYS", min=1, help="Days between two runs.")
    ] = 6,
    at: Annotated[
        str,
        typer.Option(
            "--time",
            envvar="TIME",
            help="Time of the day to run at, as HH:MM, in the local timezone (TZ).",
        ),
    ] = "02:00",
    cron: Annotated[
        str | None,
        typer.Option(
            envvar="CRON",
            help="A 5 field cron expression like '0 2 * * 1', replaces --days and "
            "--time.",
        ),
    ] = None,
    run_on_start: Annotated[
        bool,
        typer.Option(
            "--run-on-start/--no-run-on-start",
            envvar="RUN_ON_START",
            help="Also run once right at startup.",
        ),
    ] = True,
    oneshot: Annotated[
        bool,
        typer.Option(
            "--oneshot",
            envvar="ONESHOT",
            help="Run once and exit, same as the `run` command. Only here for the "
            "old ONESHOT setting.",
        ),
    ] = False,
) -> None:
    """Keep rotating the ephemeral port on a schedule, until stopped."""
    settings = _settings(ctx)

    if oneshot:
        if not run_job(settings):
            raise typer.Exit(code=1)
        return

    try:
        scheduler = build_scheduler(
            functools.partial(run_job, settings),
            days=days,
            at=at,
            cron=cron,
            run_on_start=run_on_start,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    serve(scheduler)
