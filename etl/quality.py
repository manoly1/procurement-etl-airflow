"""Data-quality checks.

Guardrails that run as their own steps — before and after load — so bad data is
caught loudly instead of silently landing in the warehouse. Each check returns a
useful value on success and raises ``QualityError`` on failure, which in the DAG
fails that task (and only that branch). This is the systematic version of the
V4-audit matrix of the original project.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd


class QualityError(ValueError):
    """Raised when a data-quality check fails."""


def unique_keys(df: pd.DataFrame, key_cols: Sequence[str]) -> int:
    """Every row must have a unique composite key. Returns the row count."""
    duplicated = df.duplicated(subset=list(key_cols), keep=False)
    n_dupes = int(duplicated.sum())
    if n_dupes:
        raise QualityError(f"{n_dupes} rows share a duplicate key on {list(key_cols)}")
    return len(df)


def not_null(df: pd.DataFrame, cols: Sequence[str]) -> int:
    """Required columns must have no nulls. Returns the row count."""
    offenders = {c: int(df[c].isna().sum()) for c in cols if df[c].isna().any()}
    if offenders:
        raise QualityError(f"null values in required columns: {offenders}")
    return len(df)


def row_count_delta(prev_n: int, cur_n: int, max_pct: float = 0.5) -> float:
    """Week-over-week row count must not swing by more than ``max_pct``.

    Returns the observed fraction. A sudden collapse or explosion usually means
    a broken source, not real business change.
    """
    if prev_n == 0:
        return 0.0
    pct = abs(cur_n - prev_n) / prev_n
    if pct > max_pct:
        raise QualityError(
            f"row count changed {pct:.0%} ({prev_n} -> {cur_n}), "
            f"over the {max_pct:.0%} limit"
        )
    return pct


def freshness(df: pd.DataFrame, report_date_col: str, expected: str) -> str:
    """Every row's report date must equal the week being processed."""
    found = set(df[report_date_col].astype(str).unique())
    if found != {str(expected)}:
        raise QualityError(
            f"stale/mismatched {report_date_col}: "
            f"found {sorted(found)}, expected {expected}"
        )
    return str(expected)
