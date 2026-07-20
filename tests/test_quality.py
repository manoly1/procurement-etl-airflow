"""Tests for the data-quality checks (on real snapshots)."""

from __future__ import annotations

import pandas as pd
import pytest

from etl.dates import report_monday
from etl.etl_log import StageTimer
from etl.quality import (
    QualityError,
    freshness,
    not_null,
    row_count_delta,
    unique_keys,
)


def test_unique_keys_passes_on_valid_snapshot(snapshot):
    assert unique_keys(snapshot, ["key"]) == len(snapshot)


def test_unique_keys_catches_duplicates(snapshot):
    dup = pd.concat([snapshot, snapshot.iloc[[0]]], ignore_index=True)
    with pytest.raises(QualityError):
        unique_keys(dup, ["key"])


def test_not_null_passes_on_key(snapshot):
    assert not_null(snapshot, ["key"]) == len(snapshot)


def test_not_null_catches_nulls(snapshot):
    bad = snapshot.copy()
    bad.loc[0, "key"] = None
    with pytest.raises(QualityError):
        not_null(bad, ["key"])


def test_row_count_delta_within_limit():
    assert row_count_delta(100, 110, max_pct=0.5) == pytest.approx(0.1)


def test_row_count_delta_catches_collapse():
    with pytest.raises(QualityError):
        row_count_delta(100, 10, max_pct=0.5)


def test_freshness_passes(snapshot):
    assert freshness(snapshot, "report_date", report_monday(29).isoformat())


def test_freshness_catches_stale(snapshot):
    bad = snapshot.copy()
    bad.loc[0, "report_date"] = "2020-01-06"
    with pytest.raises(QualityError):
        freshness(bad, "report_date", report_monday(29).isoformat())


def test_stage_timer_records_success():
    with StageTimer("transform", "dedup", rows_in=5) as timer:
        timer.rows_out = 5
    record = timer.record()
    assert record.status == "PASSED"
    assert record.rows_in == 5 and record.rows_out == 5
    assert record.duration_s >= 0


def test_stage_timer_records_failure():
    try:
        with StageTimer("load", "upsert", rows_in=3) as timer:
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert timer.record().status == "FAILED"
