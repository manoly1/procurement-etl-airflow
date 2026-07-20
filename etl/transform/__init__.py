"""Transform layer — turn a raw extract into a clean weekly snapshot.

This is the business logic of one weekly snapshot, the pandas re-imagining of the
VBA transform modules:

    * coerce numbers-as-text to real numbers (locale-aware);
    * normalize / zero-pad key columns (MaterialKey keeps its leading zeros);
    * build the composite key (POKey / PRKey);
    * drop rows whose key is incomplete (they cannot be keyed or upserted);
    * deduplicate to one row per key (CompactRowsByKey);
    * stamp ReportDate / ReportWeek from the run's week;
    * enrich via lookup joins (FillKeyByLookup -> merge).

Unlike the VBA version there is no clipboard, no xlMultiply coercion and no
Calculate — pandas does it declaratively. The new gotchas (object dtype, NaN,
copy-vs-view) are covered in the guide.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..column_resolver import DatasetConfig
from ..dates import report_monday
from ..keys import compact_rows_by_key, normalize_key

KEY_SEP = "|"


def to_numeric(series: pd.Series) -> pd.Series:
    """Coerce a numbers-as-text column to float ("1 234,50" -> 1234.5)."""

    def parse(value: object) -> float:
        if value is None:
            return np.nan
        if isinstance(value, bool):
            return float(value)
        if isinstance(value, (int, float)):
            return (
                np.nan
                if (isinstance(value, float) and value != value)
                else float(value)
            )
        text = "".join(str(value).split()).replace(",", ".")
        try:
            return float(text)
        except ValueError:
            return np.nan

    return series.map(parse)


def build_composite_key(
    df: pd.DataFrame, key_fields: tuple[str, ...]
) -> tuple[pd.Series, pd.Series]:
    """Return (key, complete_mask): the joined key and which rows have every part."""
    parts = [df[f].map(normalize_key) for f in key_fields]
    complete = pd.concat([p != "" for p in parts], axis=1).all(axis=1)
    key = parts[0] if len(parts) == 1 else parts[0].str.cat(parts[1:], sep=KEY_SEP)
    return key, complete


def enrich_rates(df: pd.DataFrame, rates: pd.DataFrame | None) -> pd.DataFrame:
    """Lookup join on currency, adding rate_to_eur and a line value in EUR."""
    if rates is None or "currency" not in df.columns:
        return df
    out = df.merge(rates, on="currency", how="left")
    if {"order_quantity", "net_price"}.issubset(out.columns):
        out["line_value_eur"] = (
            out["order_quantity"] * out["net_price"] * out["rate_to_eur"]
        )
    return out


def transform(
    df: pd.DataFrame,
    config: DatasetConfig,
    week: int,
    seeds: dict[str, pd.DataFrame] | None = None,
) -> pd.DataFrame:
    """Turn a resolved extract into the clean weekly snapshot for ``week``."""
    out = df.copy()

    # 1. numbers-as-text -> numbers
    for field in config.numeric_fields():
        if field in out.columns:
            out[field] = to_numeric(out[field])

    # 2. zero-pad key-like columns (MaterialKey keeps leading zeros)
    for field, width in config.pad_fields().items():
        if field in out.columns:
            out[field] = out[field].map(lambda v, w=width: normalize_key(v, width=w))

    # 3. composite key + drop rows whose key is incomplete
    key, complete = build_composite_key(out, config.key)
    out = out.assign(key=key)[complete].reset_index(drop=True)

    # 4. one row per key (latest wins after a stable sort)
    out = compact_rows_by_key(out, key_cols=["key"], sort_cols=["key"], keep="last")

    # 5. stamp the logical date
    out["report_date"] = report_monday(week).isoformat()
    out["report_week"] = week

    # 6. lookup enrichment
    rates = (seeds or {}).get("rates")
    out = enrich_rates(out, rates)

    return out
