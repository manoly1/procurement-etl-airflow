"""Key normalization and row compaction.

The pandas re-implementation of the VBA `NormalizeKey` and `CompactRowsByKey`
helpers — the first real pieces of the ETL core. `normalize_key` cleans a raw
key value (SAP MaterialKey keeps its leading zeros); `compact_rows_by_key`
collapses duplicate rows down to one row per composite key. Both are exercised
as katas in the guide's Module 2.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd


def normalize_key(value: object, width: int | None = None) -> str:
    """Normalize a raw key value into a clean string key.

    Trims surrounding whitespace, drops the trailing ``.0`` Excel adds when it
    reads a numeric-looking key as a float, upper-cases, and optionally
    left-pads with zeros to a fixed width (MaterialKey keeps its leading
    zeros). ``None`` / ``NaN`` / empty all normalize to ``""``.
    """
    if value is None:
        return ""
    # pandas represents missing values as float NaN, which is not equal to itself.
    if isinstance(value, float) and value != value:
        return ""
    text = str(value).strip()
    if text == "":
        return ""
    # "1000.0" (Excel read an integer key as a float) -> "1000".
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    text = text.upper()
    if width is not None:
        text = text.zfill(width)
    return text


def compact_rows_by_key(
    df: pd.DataFrame,
    key_cols: Sequence[str],
    sort_cols: Sequence[str] | None = None,
    keep: str = "last",
) -> pd.DataFrame:
    """Collapse duplicate rows to one row per key.

    Rows sharing the same values in ``key_cols`` are duplicates. When
    ``sort_cols`` is given, rows are sorted by them first (stable sort) so that
    ``keep`` ("last"/"first") picks a deterministic winner — e.g. the most
    recent snapshot line for a PO. Returns a new DataFrame; the input is not
    mutated.
    """
    if keep not in ("first", "last"):
        raise ValueError("keep must be 'first' or 'last'")
    result = df
    if sort_cols:
        # mergesort is stable: ties keep their original relative order.
        result = result.sort_values(list(sort_cols), kind="mergesort")
    result = result.drop_duplicates(subset=list(key_cols), keep=keep)
    return result.reset_index(drop=True)
