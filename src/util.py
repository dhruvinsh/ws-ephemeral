import functools
import logging

import schedule

logger = logging.getLogger("main.util")


def catch_exceptions(cancel_on_failure=False):
    """
    This decorator allows capturing errors in the schedule run and provides the option
    to cancel the job if necessary.
    """

    def catch_exceptions_decorator(job_func):
        @functools.wraps(job_func)
        def wrapper(*args, **kwargs):
            try:
                return job_func(*args, **kwargs)
            except Exception:
                import traceback

                logging.error(traceback.format_exc())
                if cancel_on_failure:
                    return schedule.CancelJob

        return wrapper

    return catch_exceptions_decorator

