"""Dirty-data archetypes.

A catalogue of the real problems the source files have, injected under flags so
tests can target each one. Every archetype here has a canonical DE fix that a
later module implements:

    date_in_row1    -> a title row above the headers (find the header row)
    numbers_as_text -> "1 234,50" instead of 1234.5 (locale-aware parsing)
    leading_zeros   -> MaterialKey as "00123456" text (preserve, don't strip)
    duplicate_rows  -> repeated rows (dedup by composite key)
    junk_rows       -> footer / total lines (drop non-data rows)
    missing_keys    -> blank key cells (validate / quarantine)

`date_in_row1` is handled by the writer; the rest transform the DataFrame here.
"""

from __future__ import annotations

import random

import pandas as pd

from .datasets import Dataset

DIRTY_ARCHETYPES: tuple[str, ...] = (
    "date_in_row1",
    "numbers_as_text",
    "leading_zeros",
    "duplicate_rows",
    "junk_rows",
    "missing_keys",
)


def default_flags(dirty_on: bool) -> set[str]:
    """All archetypes when generating a dirty file, none when clean."""
    return set(DIRTY_ARCHETYPES) if dirty_on else set()


def _messy_number(value: object, rng: random.Random) -> object:
    """Render a number as locale-messy text: 1234.5 -> "1 234,50"."""
    try:
        s = f"{float(value):,.2f}"  # "1,234.50"
    except (TypeError, ValueError):
        return value
    return s.replace(",", " ").replace(".", ",")  # "1 234,50"


def _append_junk(df: pd.DataFrame, ds: Dataset) -> pd.DataFrame:
    """Append footer / total rows that are not real data."""
    first = ds.columns[0]
    junk = [
        {c: (label if c == first else None) for c in ds.columns}
        for label in ("Total", "*** End of report ***")
    ]
    return pd.concat(
        [df, pd.DataFrame(junk, columns=list(df.columns))], ignore_index=True
    )


def apply(
    df: pd.DataFrame, ds: Dataset, flags: set[str], rng: random.Random
) -> pd.DataFrame:
    """Return a dirtied copy of ``df`` for the enabled archetypes."""
    df = df.copy()

    if "leading_zeros" in flags:
        # MaterialKey kept as zero-padded text — the value that must survive extract.
        df[ds.material_col] = df[ds.material_col].map(lambda v: str(int(v)).zfill(8))

    if "numbers_as_text" in flags:
        for col in ds.numeric_cols:
            df[col] = df[col].map(
                lambda v: _messy_number(v, rng) if rng.random() < 0.5 else v
            )

    if "duplicate_rows" in flags and len(df) > 3:
        dup = df.sample(n=3, random_state=rng.randint(0, 10**6))
        df = pd.concat([df, dup], ignore_index=True)

    if "missing_keys" in flags and len(df) > 5:
        # Blank the item part of the composite key on a couple of rows.
        col = ds.key_cols[-1]
        df[col] = df[col].astype(object)  # allow None in an otherwise-int column
        for i in rng.sample(range(len(df)), k=2):
            df.loc[i, col] = None

    if "junk_rows" in flags:
        df = _append_junk(df, ds)

    return df
