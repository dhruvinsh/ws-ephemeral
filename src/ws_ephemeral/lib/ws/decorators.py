"""Windscribe decorators."""

import functools
from typing import TYPE_CHECKING, Any, Callable

from loguru import logger

if TYPE_CHECKING:
    from .ws import Windscribe


def login_required(func: Callable):
    """Decorator for windscribe to make sure methods are protected with login."""

    @functools.wraps(func)
    def inner(*args: Any, **kwargs: Any):
        obj: "Windscribe" = args[0]

        # if any requests made and not authenticated then login first.
        if not obj.is_authenticated:
            logger.warning("requests is not authenticated, sending one.")
            obj.login()

        return func(*args, **kwargs)

    return inner
