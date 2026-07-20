"""Tests for the reporting-date helpers (logical date / backfill weeks)."""

from __future__ import annotations

from datetime import date

import pytest

from etl.dates import report_monday, week_from_logical_date, weeks_in_range


def test_week_from_logical_date() -> None:
    # Logical date = Monday of the reporting week.
    assert week_from_logical_date(date(2026, 7, 20)) == 30
    assert week_from_logical_date(date(2026, 7, 13)) == 29


def test_report_monday_and_week_roundtrip() -> None:
    for week in (25, 27, 29, 30):
        assert week_from_logical_date(report_monday(week)) == week


def test_weeks_in_range() -> None:
    assert weeks_in_range(25, 30) == [25, 26, 27, 28, 29, 30]
    assert weeks_in_range(29, 29) == [29]


def test_weeks_in_range_rejects_reversed() -> None:
    with pytest.raises(ValueError):
        weeks_in_range(30, 25)
