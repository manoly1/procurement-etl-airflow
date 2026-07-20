"""Tests for etl.keys — the NormalizeKey / CompactRowsByKey katas."""

from __future__ import annotations

import pandas as pd
import pytest

from etl.keys import compact_rows_by_key, normalize_key


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("  ab-12 ", "AB-12"),  # trim + upper
        ("1000.0", "1000"),  # Excel float artifact
        ("abc", "ABC"),
        ("", ""),
        (None, ""),
        (float("nan"), ""),
        (42, "42"),
    ],
)
def test_normalize_key_basic(raw: object, expected: str) -> None:
    assert normalize_key(raw) == expected


def test_normalize_key_width_preserves_leading_zeros() -> None:
    assert normalize_key("123", width=6) == "000123"
    assert normalize_key("  42 ", width=4) == "0042"
    # Already wide enough: width is a minimum, never truncates.
    assert normalize_key("123456", width=4) == "123456"


def test_compact_rows_by_key_keeps_latest_after_sort() -> None:
    df = pd.DataFrame(
        {
            "po": ["A", "A", "B"],
            "week": [25, 26, 25],
            "qty": [10, 99, 5],
        }
    )
    out = compact_rows_by_key(df, key_cols=["po"], sort_cols=["week"], keep="last")
    assert len(out) == 2
    # For po "A" the latest week (26) wins -> qty 99.
    assert out.loc[out["po"] == "A", "qty"].iloc[0] == 99


def test_compact_rows_by_key_composite_key() -> None:
    df = pd.DataFrame(
        {
            "po": ["A", "A", "A"],
            "item": [1, 1, 2],
            "qty": [10, 20, 30],
        }
    )
    out = compact_rows_by_key(df, key_cols=["po", "item"], keep="last")
    # (A,1) collapses to one row, (A,2) stays -> two rows total.
    assert len(out) == 2


def test_compact_rows_by_key_does_not_mutate_input() -> None:
    df = pd.DataFrame({"k": [1, 1], "v": [1, 2]})
    before = df.copy()
    compact_rows_by_key(df, key_cols=["k"])
    pd.testing.assert_frame_equal(df, before)


def test_compact_rows_by_key_rejects_bad_keep() -> None:
    with pytest.raises(ValueError):
        compact_rows_by_key(pd.DataFrame({"k": [1]}), key_cols=["k"], keep="middle")
