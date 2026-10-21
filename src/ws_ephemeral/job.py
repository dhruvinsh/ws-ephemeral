"""The job: rotate the Windscribe ephemeral port and tell qBittorrent about it."""

import logging

from .config import Settings
from .qbit import QbitManager
from .windscribe import Windscribe, WindscribeError

logger = logging.getLogger(__name__)


def rotate_port(settings: Settings) -> int:
    """Setup a new matching ephemeral port and hand it over to qBittorrent.

    Steps:
    - make sure qBittorrent is reachable, so that we never rotate a port that we
      then can't hand over
    - login to ws and setup new matching port
    - setup qbit

    Args:
        settings (Settings): The settings of the run.

    Returns:
        int: The new matching ephemeral port.
    """
    qbit_settings = settings.qbit
    qbit: QbitManager | None = None
    if qbit_settings is not None:
        try:
            qbit = QbitManager(
                host=qbit_settings.host,
                port=qbit_settings.port,
                username=qbit_settings.username,
                password=qbit_settings.password,
            )
        except Exception:
            logger.error("qBittorrent is not accessible, not touching Windscribe")
            raise

    ws = settings.windscribe
    with Windscribe(
        username=ws.username,
        password=ws.password,
        totp=ws.totp,
        cookie_file=ws.cookie_file,
        timeout=ws.timeout,
    ) as client:
        port = client.setup()
    logger.info("New ephemeral port: %s", port)

    if qbit is None or qbit_settings is None:
        logger.warning(
            "qBittorrent is not set up, read the latest doc: "
            "https://github.com/dhruvinsh/ws-ephemeral#readme"
        )
        return port

    if not qbit.set_listen_port(port):
        logger.warning("qBittorrent did not report the new port %s", port)

    if qbit_settings.private_tracker and not qbit.setup_private_tracker():
        logger.warning("qBittorrent still has dht, pex or lsd enabled")

    return port


def run_job(settings: Settings) -> bool:
    """Run `rotate_port` and report the outcome, never raises.

    Safe to hand to a scheduler, one failed run must not stop the next one.

    Args:
        settings (Settings): The settings of the run.

    Returns:
        bool: True if the port was rotated, False if anything failed.
    """
    logger.info("Running automation...")
    try:
        rotate_port(settings)
    except WindscribeError as exc:
        logger.error("Windscribe rejected the request: %s", exc)
        return False
    except Exception:
        logger.exception("Port setup failed")
        return False

    logger.info("Port setup completed..")
    return True
