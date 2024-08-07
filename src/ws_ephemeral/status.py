"""Collection of status."""

from enum import Enum


class Status(Enum):
    """Various status indicator for the function call."""

    # fmt: off
    invalid_config       = 100
    qbit_port_failed     = 101
    qbit_tracker_failed  = 102

    ws_port_updated      = 201
    qbit_port_updated    = 202
    qbit_tracker_updated = 203
    qbit_full_updated    = 204
