"""Qbit manager."""

from loguru import logger
from qbittorrentapi import Client, Version

from .decorators import qbit_supported


class QbitManager:
    """Qbittorrent manager."""

    __slots__ = ["api", "client", "logger"]

    def __init__(self, host: str, port: int, username: str, password: str) -> None:
        """QbitManager API.

        :param host: host address
        :param port: qbittorrent port number
        :param username: qbittorrent username
        "param password: qbittorrent password
        """
        self.logger = logger.bind(classname=self.__class__.__name__)

        self.client = Client(
            host,
            port,
            username,
            password,
            SIMPLE_RESPONSES=True,
            RAISE_ERROR_FOR_UNSUPPORTED_QBITTORRENT_VERSIONS=True,
        )

    def is_supported(self) -> bool:
        """Check if the qbittorrent is supported."""
        client_version: str = self.client.app.version
        return Version.is_app_version_supported(self.client.app.version)

    @qbit_supported
    def set_listen_port(self, port: int) -> bool:
        """For the given qbit instance set the listen port obtained from ws."""
        self.client.app_set_preferences({"listen_port": port})

        # lets verify if it happen or not
        current_port = self.client.application.preferences["listen_port"]
        self.logger.info(f"New setup port: {current_port}")
        return current_port == port

    @qbit_supported
    def setup_private_tracker(self) -> bool:
        """Work with private tracker related config.

        Sometimes private tracker has specific needs like,
        - disable DHT
        - disable PeX
        - disable local peer discovery
        """
        self.logger.info("Setting qbit preferences for private tracker, dht-pex-lsd")
        self.client.app_set_preferences({"dht": False, "pex": False, "lsd": False})

        dht = self.client.application.preferences["dht"]
        pex = self.client.application.preferences["pex"]
        lsd = self.client.application.preferences["lsd"]

        return not any([dht, pex, lsd])
