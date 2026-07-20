"""Tests for the Metabase BI query pack.

Each dashboard card is native SQL under bi/metabase/queries/. These tests keep
that SQL honest offline: it must parse as Postgres and reference only the dbt
marts (tables and columns), so a rename in the marts that breaks a card is
caught by the suite, not in the dashboard.
"""

from __future__ import annotations

from pathlib import Path

import pytest

sqlglot = pytest.importorskip("sqlglot")
from sqlglot import exp  # noqa: E402 - import after importorskip guard

QUERIES_DIR = Path(__file__).resolve().parent.parent / "bi" / "metabase" / "queries"

MART_TABLES = {"mart_open_po_weekly", "mart_top_suppliers"}
MART_COLUMNS = {
    "report_week",
    "report_date",
    "line_count",
    "total_quantity",
    "total_value_eur",
    "supplier",
    "value_eur",
}

QUERY_FILES = sorted(QUERIES_DIR.glob("*.sql"))


def test_query_pack_is_not_empty() -> None:
    assert QUERY_FILES, "expected SQL cards under bi/metabase/queries/"


@pytest.mark.parametrize("path", QUERY_FILES, ids=lambda p: p.name)
def test_query_parses_and_stays_within_marts(path: Path) -> None:
    tree = sqlglot.parse_one(path.read_text(), read="postgres")

    tables = {t.name for t in tree.find_all(exp.Table)}
    columns = {c.name for c in tree.find_all(exp.Column)}

    assert tables & MART_TABLES, f"{path.name} references no marts table"
    assert tables <= MART_TABLES, f"{path.name} references unknown tables"
    assert columns <= MART_COLUMNS, f"{path.name} references unknown columns"
