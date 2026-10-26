import json
from unittest.mock import Mock

import pytest

from ws_ephemeral import gluetun
from ws_ephemeral.config import GluetunSettings

SETTINGS = GluetunSettings(
    url="http://gluetun:8000/",
    api_key="test-secret",
    fixed_ports=(8080, 6881),
)


def test_sync_port_sends_fixed_and_dynamic_ports(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = Mock()
    response.status = 200
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    urlopen = Mock(return_value=response)
    monkeypatch.setattr(gluetun, "urlopen", urlopen)

    assert gluetun.sync_port(10940, SETTINGS) is True

    request = urlopen.call_args.args[0]
    assert request.full_url == "http://gluetun:8000/v1/portforward"
    assert request.get_method() == "PUT"
    assert request.get_header("X-api-key") == "test-secret"
    assert json.loads(request.data) == {"ports": [6881, 8080, 10940]}
    urlopen.assert_called_once_with(request, timeout=10)


def test_sync_port_returns_false_on_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from urllib.error import HTTPError

    monkeypatch.setattr(
        gluetun,
        "urlopen",
        Mock(
            side_effect=HTTPError(
                "http://gluetun:8000/v1/portforward",
                401,
                "Unauthorized",
                {},
                None,
            )
        ),
    )

    assert gluetun.sync_port(10940, SETTINGS) is False


@pytest.mark.parametrize("port", [0, -1, 65536])
def test_sync_port_rejects_invalid_port(port: int) -> None:
    assert gluetun.sync_port(port, SETTINGS) is False


def test_sync_port_replaces_old_dynamic_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = Mock()
    response.status = 200
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    urlopen = Mock(return_value=response)
    monkeypatch.setattr(gluetun, "urlopen", urlopen)

    assert gluetun.sync_port(10940, SETTINGS) is True
    assert gluetun.sync_port(12456, SETTINGS) is True

    first_request = urlopen.call_args_list[0].args[0]
    second_request = urlopen.call_args_list[1].args[0]

    assert json.loads(first_request.data) == {"ports": [6881, 8080, 10940]}
    assert json.loads(second_request.data) == {"ports": [6881, 8080, 12456]}
    assert 10940 not in json.loads(second_request.data)["ports"]
