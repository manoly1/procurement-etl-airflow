#!/usr/bin/env python3
"""Checkpoint 12 — the Metabase BI layer.

Metabase itself is a UI, so the reviewable artifact is the native SQL behind
each dashboard card (bi/metabase/queries/*.sql). This checkpoint validates that
SQL offline: every file parses as Postgres SQL, references only the dbt `marts`
tables, and touches only columns those marts actually expose — catching a typo
before it reaches the dashboard. Building the dashboard runs against live
Metabase (`make up`) on your machine.

Run via:  make checkpoint 12
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
QUERIES = REPO / "bi" / "metabase" / "queries"

# The mart contract these cards are allowed to depend on.
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


def main() -> int:
    print("Checkpoint 12 — Metabase BI layer")
    print("-" * 44)

    files = sorted(QUERIES.glob("*.sql")) if QUERIES.exists() else []
    if not files:
        print(f"  ✖ no query files in {QUERIES.relative_to(REPO)}/")
        print("-" * 44)
        print("STATUS: FAILED")
        return 1
    print(f"  ✔ {len(files)} dashboard queries found")

    if importlib.util.find_spec("sqlglot") is None:
        print('  ✖ sqlglot not installed (run: pip install -e ".[dev]")')
        print("-" * 44)
        print("STATUS: FAILED")
        return 1

    import sqlglot
    from sqlglot import exp

    all_ok = True
    for f in files:
        sql = f.read_text()
        try:
            tree = sqlglot.parse_one(sql, read="postgres")
        except Exception as e:  # noqa: BLE001 - report any parse error uniformly
            print(f"  ✖ {f.name}: parse error — {e}")
            all_ok = False
            continue

        tables = {t.name for t in tree.find_all(exp.Table)}
        columns = {c.name for c in tree.find_all(exp.Column)}

        bad_tables = tables - MART_TABLES
        bad_columns = columns - MART_COLUMNS
        if bad_tables:
            print(f"  ✖ {f.name}: unknown table(s) {sorted(bad_tables)}")
            all_ok = False
        elif not tables & MART_TABLES:
            print(f"  ✖ {f.name}: does not reference a marts table")
            all_ok = False
        elif bad_columns:
            print(f"  ✖ {f.name}: unknown column(s) {sorted(bad_columns)}")
            all_ok = False
        else:
            print(f"  ✔ {f.name}: valid, marts-only")

    print("      (run `make up`, connect Metabase to marts, build the dashboard)")
    print("-" * 44)
    print("STATUS: PASSED" if all_ok else "STATUS: FAILED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
