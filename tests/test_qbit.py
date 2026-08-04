"""Tests for qBittorrent authentication configuration."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from lib.qbit import QbitManager


class QbitManagerAuthenticationTests(unittest.TestCase):
    """Exercise username/password and API-key client construction."""

    @staticmethod
    def client_mock() -> MagicMock:
        """Return a client reporting a supported Web API version."""
        client = MagicMock()
        client.app_web_api_version.return_value = "2.15.0"
        return client

    def test_uses_api_key(self) -> None:
        client = self.client_mock()
        with patch("lib.qbit.Client", return_value=client) as client_constructor:
            QbitManager("qbit", 8080, api_key="qbt_secret")

        client_constructor.assert_called_once_with(
            host="qbit", port=8080, api_key="qbt_secret", SIMPLE_RESPONSES=True
        )

    def test_uses_username_and_password(self) -> None:
        client = self.client_mock()
        with patch("lib.qbit.Client", return_value=client) as client_constructor:
            QbitManager("qbit", 8080, username="admin", password="secret")

        client_constructor.assert_called_once_with(
            host="qbit",
            port=8080,
            username="admin",
            password="secret",
            SIMPLE_RESPONSES=True,
        )

    def test_rejects_multiple_authentication_methods(self) -> None:
        with self.assertRaisesRegex(ValueError, "either"):
            QbitManager(
                "qbit",
                8080,
                username="admin",
                password="secret",
                api_key="qbt_secret",
            )

    def test_requires_authentication(self) -> None:
        with self.assertRaisesRegex(ValueError, "not configured"):
            QbitManager("qbit", 8080)


if __name__ == "__main__":
    unittest.main()
