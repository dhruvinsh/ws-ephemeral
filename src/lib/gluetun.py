"""Gluetun control server client."""

import logging
from types import TracebackType
from typing import Any, Self

import httpx


class GluetunManager:
    """Synchronize forwarded ports with Gluetun's runtime firewall."""

    __slots__ = ["client", "logger"]

    def __init__(
        self,
        url: str,
        timeout: int | None = 5,
        api_key: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        if not url:
            raise ValueError("Gluetun control server URL cannot be empty")
        if bool(username) != bool(password):
            raise ValueError("Gluetun username and password must be set together")
        if api_key and username:
            raise ValueError("Use either Gluetun API key or basic authentication")

        self.logger = logging.getLogger(self.__class__.__name__)
        headers = {"Accept": "application/json"}
        if api_key:
            headers["X-API-Key"] = api_key

        auth = None
        if username and password:
            auth = httpx.BasicAuth(username, password)

        self.client = httpx.Client(
            base_url=url.rstrip("/"),
            headers=headers,
            auth=auth,
            timeout=timeout,
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def get_forwarded_ports(self) -> list[int]:
        """Return ports currently allowed through Gluetun's VPN firewall."""
        response = self.client.get("/v1/portforward")
        response.raise_for_status()
        data: dict[str, Any] = response.json()

        ports = data.get("ports")
        if ports is None:
            port = data.get("port")
            ports = [] if port in (None, 0) else [port]

        if not isinstance(ports, list) or any(
            isinstance(port, bool)
            or not isinstance(port, int)
            or not 1 <= port <= 65535
            for port in ports
        ):
            raise ValueError("Gluetun returned an invalid forwarded ports response")

        return ports

    def set_forwarded_port(self, port: int) -> bool:
        """Replace Gluetun's forwarded ports with the Windscribe port."""
        if (
            isinstance(port, bool)
            or not isinstance(port, int)
            or not 1 <= port <= 65535
        ):
            raise ValueError("Forwarded port must be between 1 and 65535")

        response = self.client.put("/v1/portforward", json={"ports": [port]})
        response.raise_for_status()

        forwarded_ports = self.get_forwarded_ports()
        if forwarded_ports != [port]:
            raise RuntimeError(
                "Gluetun did not report the requested forwarded port: "
                f"expected {[port]}, got {forwarded_ports}"
            )

        self.logger.info("Gluetun VPN firewall port updated: %s", port)
        return True
