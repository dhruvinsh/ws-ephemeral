"""Scheduling of the port rotation."""

import logging
import signal
from collections.abc import Callable
from datetime import datetime, timedelta
from types import FrameType

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

SCHEDULED_JOB = "rotate-port"
ON_START_JOB = "rotate-port-on-start"

# a run that could not start on time (busy host, suspended VM) still goes ahead if it
# is at most this late, instead of being silently skipped
MISFIRE_GRACE_SECONDS = 3600


def parse_time(value: str) -> tuple[int, int]:
    """Parse a time of day.

    Args:
        value (str): The time as HH:MM.

    Returns:
        tuple[int, int]: The hour and the minute.

    Raises:
        ValueError: If the value is not a valid time.
    """
    try:
        parsed = datetime.strptime(value, "%H:%M")
    except ValueError as exc:
        raise ValueError(f"invalid time {value!r}, expected HH:MM like 02:00") from exc
    return parsed.hour, parsed.minute


def build_trigger(
    *, days: int, at: str, cron: str | None, now: datetime
) -> BaseTrigger:
    """Build the trigger for the recurring job.

    Without a cron expression the job runs every `days` days at `at`, the first time
    being `days` days from now. That matches an ephemeral port living for a week and
    a run at startup (see `build_scheduler`) having just renewed it.

    Args:
        days (int): Days between two runs.
        at (str): Time of the day to run at, as HH:MM.
        cron (str | None): A 5 field cron expression, replaces `days` and `at`.
        now (datetime): The current time, its timezone is the timezone of the trigger.

    Returns:
        BaseTrigger: The trigger.

    Raises:
        ValueError: If the time or the cron expression is invalid.
    """
    if cron is not None:
        return CronTrigger.from_crontab(cron, timezone=now.tzinfo)

    hour, minute = parse_time(at)
    first = (now + timedelta(days=days)).replace(
        hour=hour, minute=minute, second=0, microsecond=0
    )
    return IntervalTrigger(days=days, start_date=first, timezone=now.tzinfo)


def build_scheduler(
    job: Callable[[], object],
    *,
    days: int,
    at: str,
    cron: str | None,
    run_on_start: bool,
) -> BlockingScheduler:
    """Build the scheduler, without starting it.

    Args:
        job (Callable[[], object]): What to run.
        days (int): Days between two runs.
        at (str): Time of the day to run at, as HH:MM.
        cron (str | None): A 5 field cron expression, replaces `days` and `at`.
        run_on_start (bool): Also run once as soon as the scheduler starts.

    Returns:
        BlockingScheduler: The scheduler.

    Raises:
        ValueError: If the time or the cron expression is invalid.
    """
    scheduler = BlockingScheduler()
    now = datetime.now(scheduler.timezone)
    trigger = build_trigger(days=days, at=at, cron=cron, now=now)

    scheduler.add_job(
        job,
        trigger,
        id=SCHEDULED_JOB,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=MISFIRE_GRACE_SECONDS,
    )
    if run_on_start:
        # no trigger means run once, right away
        scheduler.add_job(job, id=ON_START_JOB, max_instances=1)

    if cron is not None:
        logger.info("Schedule is setup with cron %r", cron)
    else:
        logger.info("Schedule is setup to run every %s day(s) at %s", days, at)
    logger.info("Next scheduled run: %s", trigger.get_next_fire_time(None, now))

    return scheduler


def serve(scheduler: BlockingScheduler) -> None:
    """Run the scheduler until it is told to stop (CTRL-C or `docker stop`).

    Args:
        scheduler (BlockingScheduler): The scheduler to run.
    """

    def stop(signum: int, _frame: FrameType | None) -> None:
        logger.info("Received %s, shutting down", signal.Signals(signum).name)
        if scheduler.running:
            scheduler.shutdown(wait=False)

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    scheduler.start()
