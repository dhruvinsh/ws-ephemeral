"""
Collection of some helper function for the main program
"""
from typing import Optional


def validate_port(value: Optional[str]) -> int:
    """helps to validate port number.
    it need to be withing 2000 to 65365"""
    if value is None:
        raise ValueError("Valid port nubmer is required")

    port = int(value.strip())
    if 2000 > port or 65365 < port:
        raise ValueError("Valid port number need to be within 2000 to 65365 port range")

    return port


def to_seconds(days: int) -> int:
    """converts number of day to seconds"""
    return days * 24 * 3600
