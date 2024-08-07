"""Cli application."""

from __future__ import annotations

import typer

from ws_ephemeral.cfg import config
from ws_ephemeral.runner import private_tracker as ws_private_tracker
from ws_ephemeral.runner import remaining_time as ws_remaining_time
from ws_ephemeral.runner import renew_port as ws_renew_port
from ws_ephemeral.runner import renew_qbit as ws_renew_qbit
from ws_ephemeral.status import Status

cli = typer.Typer()


@cli.command()
def renew(qbit: bool = True, oneshot: bool = config.ONESHOT, forever: bool = False) -> None:
    """Renew the windscribe port."""
    from ws_ephemeral.jobs import jobs

    ret = ws_renew_port()

    if ret.status != Status.ws_port_updated:
        return

    # NOTE: adding legacy support with QBIT_FOUND
    # TODO: need to remoe QBIT_FOUND support with better flag
    if (qbit or config.QBIT_FOUND) and ret.port is not None:
        _ = ws_renew_qbit(ret.port)

    # NOTE: forever gets higher priority
    if oneshot and not forever:
        return

    if forever:
        jobs()


@cli.command()
def tracker() -> None:
    """Setup qbit for private tracker."""
    ws_private_tracker()


@cli.command()
def check() -> None:
    """Get the current renewal status."""
    ws_remaining_time()
