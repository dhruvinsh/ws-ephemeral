"""Module that run the setup for windscrib's ephemeral port."""

from __future__ import annotations

from loguru import logger

from ws_ephemeral.cfg import config
from ws_ephemeral.lib import QbitManager, Windscribe
from ws_ephemeral.lib.decorators import catch_exceptions
from ws_ephemeral.model import Renewal

from .status import Status


@catch_exceptions(cancel_on_failure=False)
def renew_port() -> Renewal:
    """Renew ephemeral port on windscribe"""
    # return {"status": Status.ws_port_updated, "port": 10047}
    with Windscribe(username=config.WS_USERNAME, password=config.WS_PASSWORD) as ws:
        csrf = ws.get_csrf()
        ws.delete_ephm_port(csrf)
        port = ws.set_matching_port(csrf)

    logger.success(f"Ephemeral port renewal complete -> {port}")
    return Renewal(status=Status.ws_port_updated, port=port)


@catch_exceptions(cancel_on_failure=False)
def remaining_time():
    """Get the remaining time in renewal."""
    ws = Windscribe(username=config.WS_USERNAME, password=config.WS_PASSWORD)
    logger.info(ws.get_remaining_time())
    ws.close()


@catch_exceptions(cancel_on_failure=False)
def renew_qbit(port: int) -> Renewal:
    """Renew qBitTorrent port."""
    if None in [config.QBIT_USERNAME, config.QBIT_PASSWORD]:
        logger.warning(
            "Read the latest doc: https://github.com/dhruvinsh/ws-ephemeral#readme",
        )
        return Renewal(status=Status.invalid_config, port=port)

    try:
        qbit = QbitManager(
            host=config.QBIT_HOST,
            port=config.QBIT_PORT,
            username=config.QBIT_USERNAME,
            password=config.QBIT_PASSWORD,
        )
        qbit.set_listen_port(port)
    except Exception:
        logger.exception("not able to work with qBitTorrent.")
        return Renewal(status=Status.qbit_port_failed, port=port)

    return Renewal(status=Status.qbit_port_updated, port=port)


@catch_exceptions(cancel_on_failure=False)
def private_tracker() -> None:
    """Disable private tracker related feature."""
    if None in [config.QBIT_USERNAME, config.QBIT_PASSWORD]:
        logger.warning(
            "Read the latest doc: https://github.com/dhruvinsh/ws-ephemeral#readme",
        )

    try:
        qbit = QbitManager(
            host=config.QBIT_HOST,
            port=config.QBIT_PORT,
            username=config.QBIT_USERNAME,
            password=config.QBIT_PASSWORD,
        )
        ret = qbit.setup_private_tracker()
    except Exception:
        logger.exception("not able to work with qBitTorrent.")
        return

    if ret:
        logger.success("Private tracker setup complete.")
    else:
        logger.error("Privater tracker setup failed.")
