"""Tests for the load layer.

The unit tests need no database: they check SQL generation and engine wiring.
The idempotency integration test runs only when DATABASE_URL points at a live
Postgres (see check_module_06 for the full end-to-end).
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import insert

from etl.load import build_upsert_sql, get_engine


def test_build_upsert_sql_structure() -> None:
    sql = build_upsert_sql("open_po", ["report_week", "key", "po_number", "net_price"])
    assert 'INSERT INTO raw."open_po"' in sql
    assert 'FROM staging."open_po"' in sql
    assert 'ON CONFLICT ("report_week", "key")' in sql
    assert "DO UPDATE SET" in sql
    assert '"po_number" = EXCLUDED."po_number"' in sql
    assert '"net_price" = EXCLUDED."net_price"' in sql
    # key columns are never in the SET clause
    assert '"key" = EXCLUDED' not in sql


def test_build_upsert_do_nothing_when_only_keys() -> None:
    sql = build_upsert_sql("x", ["report_week", "key"])
    assert "DO NOTHING" in sql
    assert "DO UPDATE" not in sql


def test_get_engine_requires_url(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError):
        get_engine()


def test_get_engine_parses_url_without_connecting() -> None:
    engine = get_engine("postgresql+psycopg2://u:p@localhost:5432/db")
    assert engine.url.database == "db"
    assert engine.url.host == "localhost"


def test_postgres_upsert_compiles_to_on_conflict() -> None:
    md = MetaData()
    table = Table(
        "open_po",
        md,
        Column("report_week", Integer, primary_key=True),
        Column("key", String, primary_key=True),
        Column("net_price", String),
        schema="raw",
    )
    stmt = insert(table).values(report_week=29, key="k", net_price="1")
    stmt = stmt.on_conflict_do_update(
        index_elements=["report_week", "key"],
        set_={"net_price": stmt.excluded.net_price},
    )
    compiled = str(stmt.compile(dialect=postgresql.dialect()))
    assert "ON CONFLICT" in compiled
    assert "DO UPDATE SET" in compiled


@pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"), reason="needs a running Postgres"
)
def test_idempotent_load_integration() -> None:
    import tempfile

    from datagen.generate import generate_file
    from datagen.seeds import build_seeds
    from etl.load import count_rows, load_snapshot
    from etl.pipeline import build_snapshot_for

    engine = get_engine()
    with tempfile.TemporaryDirectory() as tmp:
        path = generate_file("open_po", 29, dirty_on=True, out_dir=tmp)
        snap = build_snapshot_for("open_po", path, 29, seeds=build_seeds())
        load_snapshot(snap, "open_po", engine)
        first = count_rows(engine, "open_po")
        load_snapshot(snap, "open_po", engine)
        second = count_rows(engine, "open_po")
        assert first == second  # re-loading a week does not add rows
