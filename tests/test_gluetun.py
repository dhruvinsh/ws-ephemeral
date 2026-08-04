"""Tests for the Gluetun control server client."""

import base64
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from lib.gluetun import GluetunManager


class GluetunManagerTests(unittest.TestCase):
    """Exercise port synchronization and authentication behavior."""

    @staticmethod
    def manager_with_client(client: httpx.Client) -> GluetunManager:
        """Build a manager whose HTTP calls use a mock transport."""
        with patch("lib.gluetun.httpx.Client", return_value=client):
            return GluetunManager("http://gluetun:8000")

    def test_sets_and_verifies_forwarded_port(self) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            if request.method == "PUT":
                return httpx.Response(200)
            return httpx.Response(200, json={"port": 49152, "ports": [49152]})

        client = httpx.Client(
            base_url="http://gluetun:8000", transport=httpx.MockTransport(handler)
        )

        with self.manager_with_client(client) as gluetun:
            self.assertTrue(gluetun.set_forwarded_port(49152))

        self.assertEqual([request.method for request in requests], ["PUT", "GET"])
        self.assertEqual(json.loads(requests[0].content), {"ports": [49152]})

    def test_supports_legacy_single_port_response(self) -> None:
        client = httpx.Client(
            base_url="http://gluetun:8000",
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, json={"port": 49152})
            ),
        )

        with self.manager_with_client(client) as gluetun:
            self.assertEqual(gluetun.get_forwarded_ports(), [49152])

    def test_raises_when_verification_does_not_match(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "PUT":
                return httpx.Response(200)
            return httpx.Response(200, json={"port": 40000, "ports": [40000]})

        client = httpx.Client(
            base_url="http://gluetun:8000", transport=httpx.MockTransport(handler)
        )

        with (
            self.manager_with_client(client) as gluetun,
            self.assertRaisesRegex(RuntimeError, "did not report"),
        ):
            gluetun.set_forwarded_port(49152)

    def test_rejects_invalid_port(self) -> None:
        with GluetunManager("http://gluetun:8000") as gluetun:
            for port in (0, 65536, True):
                with self.subTest(port=port), self.assertRaises(ValueError):
                    gluetun.set_forwarded_port(port)

    def test_sends_api_key(self) -> None:
        with patch("lib.gluetun.httpx.Client") as client_constructor:
            manager = GluetunManager("http://gluetun:8000", api_key="secret")

        manager.close()
        headers = client_constructor.call_args.kwargs["headers"]
        self.assertEqual(headers["X-API-Key"], "secret")

    def test_sends_basic_authentication(self) -> None:
        with patch("lib.gluetun.httpx.Client") as client_constructor:
            manager = GluetunManager(
                "http://gluetun:8000", username="user", password="password"
            )

        auth = client_constructor.call_args.kwargs["auth"]
        request = httpx.Request("GET", "http://gluetun:8000/v1/portforward")
        authenticated_request = next(auth.auth_flow(request))
        token = base64.b64encode(b"user:password").decode()
        self.assertEqual(
            authenticated_request.headers["Authorization"], f"Basic {token}"
        )
        manager.close()

    def test_rejects_ambiguous_authentication(self) -> None:
        with self.assertRaisesRegex(ValueError, "either"):
            GluetunManager(
                "http://gluetun:8000",
                api_key="secret",
                username="user",
                password="password",
            )

    def test_propagates_control_server_error(self) -> None:
        client = httpx.Client(
            base_url="http://gluetun:8000",
            transport=httpx.MockTransport(lambda _: httpx.Response(405)),
        )

        with (
            self.manager_with_client(client) as gluetun,
            self.assertRaises(httpx.HTTPStatusError),
        ):
            gluetun.set_forwarded_port(49152)


if __name__ == "__main__":
    unittest.main()
