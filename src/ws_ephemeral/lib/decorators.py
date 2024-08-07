"""Decorator to protect windscribe methods."""

import functools
from typing import TYPE_CHECKING

import schedule
from loguru import logger

if TYPE_CHECKING:
    pass


def catch_exceptions(cancel_on_failure=False):
    """This decorator allow to capture the error in the schedule run and provide option
    if job cancellation require.
    """

    def catch_exceptions_decorator(job_func):
        @functools.wraps(job_func)
        def wrapper(*args, **kwargs):
            try:
                return job_func(*args, **kwargs)
            except Exception:
                logger.exception("Error occurred.")
                if cancel_on_failure:
                    return schedule.CancelJob

        return wrapper

    return catch_exceptions_decorator
