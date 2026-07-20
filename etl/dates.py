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
