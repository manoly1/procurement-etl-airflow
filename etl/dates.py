"""Reporting-date helpers.

The pipeline's logical date is the Monday of the reporting ISO week — the direct
analogue of the project's ``ReportDate = Monday of the sheet's week`` rule (and,
later, of Airflow's ``data_interval_start``). Kept tiny and dependency-free so
both the ETL core and the generator can share it.
"""

from __future__ import annotations

from datetime import date

DEFAULT_YEAR = 2026


def report_monday(week: int, year: int = DEFAULT_YEAR) -> date:
    """Monday of the given ISO week."""
    return date.fromisocalendar(year, week, 1)


def iso_week(day: date) -> int:
    """ISO week number of a date."""
    return day.isocalendar().week


def week_from_logical_date(logical_date: date) -> int:
    """ISO week of Airflow's logical date (``data_interval_start``).

    The scheduler's logical date *is* the reporting week — the same idea as
    ``ReportDate = Monday of the sheet's week``, not the day the job happened to
    run. Accepts anything with ``.isocalendar()`` (date, datetime, pendulum).
    """
    return logical_date.isocalendar()[1]


def weeks_in_range(start_week: int, end_week: int) -> list[int]:
    """Inclusive list of weeks to backfill — the analogue of ``*_SelectedWeeks``."""
    if end_week < start_week:
        raise ValueError("end_week must be >= start_week")
    return list(range(start_week, end_week + 1))
