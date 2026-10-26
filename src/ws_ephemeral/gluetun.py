"""Synchronize qBittorrent's listening port with Gluetun's runtime firewall."""

import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import GluetunSettings

logger = logging.getLogger(__name__)


def sync_port(port: int, settings: GluetunSettings) -> bool:
    """Allow the fixed ports and the current dynamic port in Gluetun."""
    try:
        ports = set(settings.fixed_ports)
        ports.add(int(port))
        if any(value < 1 or value > 65535 for value in ports):
            raise ValueError("port outside valid range")
    except TypeError, ValueError:
        logger.error("Invalid Gluetun port configuration")
        return False

    payload = json.dumps({"ports": sorted(ports)}).encode("utf-8")
    request = Request(
        f"{settings.url.rstrip('/')}/v1/portforward",
        data=payload,
        headers={
            "X-API-Key": settings.api_key,
            "Content-Type": "application/json",
        },
        method="PUT",
    )

    try:
        with urlopen(request, timeout=10) as response:
            if response.status not in (200, 204):
                logger.error("Gluetun returned HTTP %s", response.status)
                return False
        logger.info("Gluetun firewall synchronized for port %s", port)
        return True
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        logger.warning("Could not synchronize Gluetun firewall: %s", exc)
        return False
