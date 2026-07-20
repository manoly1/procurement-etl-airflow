"""Load layer — staging table -> idempotent UPSERT into Postgres.

The DE equivalent of SQLUploadEngine: instead of ADODB batches with PK-skip
logic, we bulk-load the snapshot into a transient ``staging`` table, then
``INSERT ... SELECT ... ON CONFLICT (report_week, key) DO UPDATE``. Re-running a
week updates the existing rows rather than appending them — the whole point is
**idempotency**: the same week loaded twice leaves the same number of rows.
"""

from __future__ import annotations

import os
from collections.abc import Sequence

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

DEFAULT_KEY: tuple[str, ...] = ("report_week", "key")


def get_engine(url: str | None = None) -> Engine:
    """Create a SQLAlchemy engine from ``url`` or the DATABASE_URL env var.

    ``create_engine`` is lazy — no connection is opened until the engine is
    used — so this is safe to call without a running database.
    """
    url = url or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set (e.g. postgresql+psycopg2://etl:etl@localhost:5432/procurement)"
        )
    return create_engine(url, future=True)


def build_upsert_sql(
    dataset: str,
    columns: Sequence[str],
    key_cols: Sequence[str] = DEFAULT_KEY,
    src_schema: str = "staging",
    dst_schema: str = "raw",
) -> str:
    """Build the ``INSERT ... SELECT ... ON CONFLICT DO UPDATE`` statement."""
    cols = list(columns)
    key = list(key_cols)
    col_list = ", ".join(f'"{c}"' for c in cols)
    non_key = [c for c in cols if c not in key]
    if not non_key:
        # Nothing to update — insert new keys, ignore conflicts.
        do_clause = "DO NOTHING"
    else:
        set_list = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in non_key)
        do_clause = f"DO UPDATE SET {set_list}"
    conflict = ", ".join(f'"{c}"' for c in key)
    return (
        f'INSERT INTO {dst_schema}."{dataset}" ({col_list})\n'
        f'SELECT {col_list} FROM {src_schema}."{dataset}"\n'
        f"ON CONFLICT ({conflict}) {do_clause};"
    )


def load_snapshot(
    df: pd.DataFrame,
    dataset: str,
    engine: Engine,
    key_cols: Sequence[str] = DEFAULT_KEY,
    chunksize: int = 1000,
) -> int:
    """Load a snapshot idempotently; return the number of rows staged.

    1. bulk-write the snapshot into ``staging.<dataset>`` (chunked multi-insert);
    2. UPSERT staging into ``raw.<dataset>`` keyed on ``key_cols``.
    """
    df.to_sql(
        dataset,
        engine,
        schema="staging",
        if_exists="replace",
        index=False,
        chunksize=chunksize,
        method="multi",
    )
    upsert = build_upsert_sql(dataset, list(df.columns), key_cols)
    with engine.begin() as conn:
        conn.execute(text(upsert))
    return len(df)


def count_rows(engine: Engine, dataset: str, schema: str = "raw") -> int:
    """Row count of a target table (used to check idempotency)."""
    with engine.connect() as conn:
        result = conn.execute(text(f'SELECT count(*) FROM {schema}."{dataset}"'))
        return int(result.scalar_one())
