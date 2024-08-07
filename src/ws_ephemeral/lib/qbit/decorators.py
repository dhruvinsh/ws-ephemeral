"""QbitTorrent decorator."""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Callable

from loguru import logger

if TYPE_CHECKING:
    from .manager import QbitManager


def qbit_supported(func: Callable[[], None]):
    """Decorator for qbittorrent api to make sure api are supported."""

    @functools.wraps(func)
    def inner(*args: QbitManager, **kwargs: str):
        obj = args[0]

        if not obj.is_supported():
            logger.warning("Can't process qbittorent changes, version not supported.")
            return
        return func(*args, **kwargs)

    return inner
