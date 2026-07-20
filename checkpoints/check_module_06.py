#!/usr/bin/env python3
"""Checkpoint 6 — load & idempotency.

Requires a running Postgres (``make up``). Loads the W29 snapshot for both
datasets twice and confirms the row count does not change — the idempotency
exam that closes Stage 2.

Run via:  make checkpoint 6
"""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))


def main() -> int:
    print("Checkpoint 6 — load & idempotency")
    print("-" * 44)

    for mod in ("pandas", "sqlalchemy", "psycopg2", "faker", "yaml", "openpyxl"):
        if importlib.util.find_spec(mod) is None:
            print(f'  ✖ {mod} not installed (run: pip install -e ".[dev]")')
            print("-" * 44)
            print("STATUS: FAILED")
            return 1

    url = os.environ.get("DATABASE_URL")
    if not url:
        print("  ✖ DATABASE_URL not set")
        print("    start Postgres (`make up`), set DATABASE_URL, see .env.example")
        print("-" * 44)
        print("STATUS: FAILED")
        return 1

    from sqlalchemy import text

    from datagen.generate import generate_file
    from datagen.seeds import build_seeds
    from etl.load import count_rows, get_engine, load_snapshot
    from etl.pipeline import build_snapshot_for

    try:
        engine = get_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - connection failure is a checkpoint failure
        print(f"  ✖ cannot connect to Postgres: {exc}")
        print("    start it with `make up` (docker compose up -d)")
        print("-" * 44)
        print("STATUS: FAILED")
        return 1

    config_dir = str(REPO / "config" / "datasets")
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        for name in ("open_po", "all_prs"):
            path = generate_file(name, 29, dirty_on=True, out_dir=tmp)
            snap = build_snapshot_for(
                name, path, 29, seeds=build_seeds(), config_dir=config_dir
            )
            load_snapshot(snap, name, engine)
            first = count_rows(engine, name)
            load_snapshot(snap, name, engine)
            second = count_rows(engine, name)
            good = first == second and first > 0
            ok = ok and good
            glyph = "✔" if good else "✖"
            print(f"  {glyph} {name}: {first} rows, re-load unchanged (idempotent)")

    print("-" * 44)
    print("STATUS: PASSED" if ok else "STATUS: FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
