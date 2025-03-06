import functools
import logging
from typing import TYPE_CHECKING, Any, Callable, TypeVar

T = TypeVar("T")

if TYPE_CHECKING:
    from ws import Windscribe


def login_required(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to ensure the Windscribe object is authenticated before executing the method.

    Args:
        func (Callable[..., T]): The function to be decorated.

    Returns:
        Callable[..., T]: The decorated function.
    """
    def inner(*args: Any, **kwargs: Any) -> T:
        obj: "Windscribe" = args[0]

        # if any requests made and not authenticated then login first.
        if not obj.is_authenticated:
            logging.warning("Request is not authenticated, logging in.")
            obj.login()

        return func(*args, **kwargs)

    return inner
