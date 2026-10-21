from datetime import datetime, timedelta

import pytest
from apscheduler.job import Job
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from ws_ephemeral.scheduler import (
    ON_START_JOB,
    SCHEDULED_JOB,
    build_scheduler,
    parse_time,
)


def build(
    *,
    days: int = 6,
    at: str = "02:30",
    cron: str | None = None,
    run_on_start: bool = True,
) -> BlockingScheduler:
    return build_scheduler(
        lambda: None, days=days, at=at, cron=cron, run_on_start=run_on_start
    )


def jobs(scheduler: BlockingScheduler) -> dict[str, Job]:
    return {job.id: job for job in scheduler.get_jobs()}


def test_runs_every_n_days_at_the_given_time() -> None:
    trigger = jobs(build())[SCHEDULED_JOB].trigger

    assert isinstance(trigger, IntervalTrigger)
    assert trigger.interval == timedelta(days=6)
    assert (trigger.start_date.hour, trigger.start_date.minute) == (2, 30)
    # the first scheduled run is days from now, the run at startup covers until then
    assert trigger.start_date > datetime.now(trigger.start_date.tzinfo) + timedelta(
        days=5
    )


def test_runs_once_right_at_startup_by_default() -> None:
    assert isinstance(jobs(build())[ON_START_JOB].trigger, DateTrigger)


def test_startup_run_can_be_turned_off() -> None:
    assert set(jobs(build(run_on_start=False))) == {SCHEDULED_JOB}


def test_cron_expression_replaces_days_and_time() -> None:
    trigger = jobs(build(cron="0 2 * * 1"))[SCHEDULED_JOB].trigger

    assert isinstance(trigger, CronTrigger)


@pytest.mark.parametrize("at", ["25:00", "02:60", "2am", ""])
def test_bad_time_is_rejected(at: str) -> None:
    with pytest.raises(ValueError, match="HH:MM"):
        build(at=at)


def test_bad_cron_expression_is_rejected() -> None:
    with pytest.raises(ValueError):
        build(cron="not a cron")


def test_parse_time() -> None:
    assert parse_time("02:05") == (2, 5)
    assert parse_time("23:59") == (23, 59)
