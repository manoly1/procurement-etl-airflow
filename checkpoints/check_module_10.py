#!/usr/bin/env python3
"""Checkpoint 10 — the dbt transformation layer.

Validates the dbt project *structurally* without a warehouse: `dbt parse`
compiles every model, resolves each `ref()`/`source()`, and builds the graph
of models, seeds and tests. That is the offline gate — "the project is wired
correctly." The end-to-end gate (`dbt build` materializing views/tables and
running the data tests) needs a live Postgres and is exercised by `make dbt`
after `make up`.

Run via:  make checkpoint 10
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DBT_DIR = REPO / "dbt"

# Nodes we expect the parse to register — the shape of the layer.
EXPECTED_MODELS = {
    "stg_open_po",
    "stg_all_prs",
    "mart_open_po_weekly",
    "mart_top_suppliers",
}


def main() -> int:
    print("Checkpoint 10 — dbt transformation layer")
    print("-" * 44)

    # 1. The project files exist and are laid out as expected.
    required = [
        DBT_DIR / "dbt_project.yml",
        DBT_DIR / "profiles.yml",
        DBT_DIR / "models" / "staging" / "sources.yml",
        DBT_DIR / "seeds" / "rates.csv",
    ]
    missing = [p.relative_to(REPO) for p in required if not p.exists()]
    if missing:
        for p in missing:
            print(f"  ✖ missing {p}")
        print("-" * 44)
        print("STATUS: FAILED")
        return 1
    print(f"  ✔ dbt project files present ({DBT_DIR.relative_to(REPO)}/)")

    # 2. dbt itself must be installed.
    if shutil.which("dbt") is None:
        print('  ✖ dbt not installed (run: pip install -e ".[dbt]")')
        print("      then re-run: make checkpoint 10")
        print("-" * 44)
        print("STATUS: FAILED")
        return 1

    # 3. `dbt parse` compiles the graph offline — no warehouse needed.
    proc = subprocess.run(
        ["dbt", "parse", "--profiles-dir", ".", "--project-dir", "."],
        cwd=DBT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    parse_ok = proc.returncode == 0
    print(f"  {'✔' if parse_ok else '✖'} dbt parse (graph compiles, refs resolve)")
    if not parse_ok:
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-3:]
        for line in tail:
            print(f"      {line}")
        print("-" * 44)
        print("STATUS: FAILED")
        return 1

    # 4. The expected models are registered in the parsed graph.
    listed = subprocess.run(
        [
            "dbt",
            "list",
            "--resource-type",
            "model",
            "--profiles-dir",
            ".",
            "--project-dir",
            ".",
        ],
        cwd=DBT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    found = {
        line.rsplit(".", 1)[-1]
        for line in listed.stdout.splitlines()
        if line.startswith("procurement.")
    }
    models_ok = EXPECTED_MODELS.issubset(found)
    got = ", ".join(sorted(EXPECTED_MODELS & found)) or "none"
    print(f"  {'✔' if models_ok else '✖'} models registered: {got}")

    print("      (run `make up && make dbt` to build + test against Postgres)")

    ok = parse_ok and models_ok
    print("-" * 44)
    print("STATUS: PASSED" if ok else "STATUS: FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
