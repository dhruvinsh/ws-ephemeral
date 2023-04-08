"""
Qbit manager
"""

import logging
from typing import Any

from qbittorrentapi import Client
from semver.version import Version


class QbitManager:
    __slots__ = ["api", "client", "logger"]

    def __init__(self, host: str, port: int, username: str, password: str) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

        self.client = Client(host, port, username, password, SIMPLE_RESPONSES=True)
        self.api = Version.parse(self.client.app_web_api_version())

    def __getattribute__(self, __name: str) -> Any:
        """
        protector to make sure correct qbit web api supported
        """
        if __name in ["set_listen_port", "setup_private_tracker"]:
            self.logger.debug("API version: %s", self.api)
            if self.api.minor < 6:
                raise ValueError(
                    "Cannot work with qbit, minimum required version is: 4.0.0"
                )

        return object.__getattribute__(self, __name)

    def set_listen_port(self, port: int) -> bool:
        """
        for the given qbit instance set the listen port obtained from ws
        """
        self.client.app_set_preferences({"listen_port": port})

        # lets verify if it happen or not
        current_port = self.client.application.preferences["listen_port"]
        self.logger.info("New setup port: %s", current_port)
        return current_port == port

    def setup_private_tracker(self) -> bool:
        """
        sometimes private tracker has specific needs like,
        - disable DHT
        - disable PeX
        - disable local peer discovery
        """
        self.logger.info("Setting qbit preferences for private tracker")
        self.client.app_set_preferences({"dht": False, "pex": False, "lsd": False})

        dht = self.client.application.preferences["dht"]
        pex = self.client.application.preferences["pex"]
        lsd = self.client.application.preferences["lsd"]

        return not any([dht, pex, lsd])
