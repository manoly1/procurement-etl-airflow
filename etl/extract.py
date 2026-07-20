"""Extract layer — read an untrusted xlsx into a clean DataFrame.

Two problems the raw files have (see the datagen archetypes) are solved here:
the header row may not be the first row (a report-date title can sit above it),
and there may be footer / junk rows below the data. `read_extract` finds the
header row (the analogue of DetectHeaderRow), slices the data out, drops the
junk, and — via the column resolver — returns a frame with canonical column
names.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .column_resolver import DatasetConfig, apply_resolution, resolve_columns


def read_raw(path: str | Path) -> pd.DataFrame:
    """Read every cell as-is, with no header inference."""
    return pd.read_excel(path, header=None, dtype=object)


def find_header_row(
    raw: pd.DataFrame, known_headers: set[str], max_scan: int = 15
) -> int:
    """Return the 0-based index of the row that looks like the header row.

    The header row is the scanned row with the most cells matching a known
    header name. Ties are broken toward the earliest row.
    """
    best_row, best_hits = 0, -1
    limit = min(max_scan, len(raw))
    for i in range(limit):
        values = {str(v).strip() for v in raw.iloc[i].tolist() if v is not None}
        hits = len(values & known_headers)
        if hits > best_hits:
            best_row, best_hits = i, hits
    return best_row


def drop_junk_rows(df: pd.DataFrame, min_filled: int = 2) -> pd.DataFrame:
    """Drop footer / junk rows: rows with fewer than ``min_filled`` non-empty cells.

    Real data rows fill many columns; footer lines ("Total", "*** End ***")
    fill only one. Rows with a merely-missing key still have most cells filled,
    so they survive here (they are handled later by data-quality checks).
    """
    filled = df.notna().sum(axis=1)
    return df[filled >= min_filled].reset_index(drop=True)


def read_extract(path: str | Path, config: DatasetConfig) -> pd.DataFrame:
    """Read a file and return a frame with canonical columns.

    header detection -> slice -> drop junk -> resolve/rename columns.
    """
    raw = read_raw(path)
    header_idx = find_header_row(raw, config.known_headers())
    headers = [
        str(v).strip() if v is not None else v for v in raw.iloc[header_idx].tolist()
    ]

    body = raw.iloc[header_idx + 1 :].copy()
    body.columns = headers
    body = body.reset_index(drop=True)
    body = drop_junk_rows(body)

    resolution = resolve_columns(body.columns, config)
    return apply_resolution(body, resolution)
