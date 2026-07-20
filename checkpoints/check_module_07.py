#!/usr/bin/env python3
"""Checkpoint 7 — the Airflow DAG parses and is registered.

The DAG file's syntax is always checked here. A full parse (DagBag) needs
Airflow, which lives in the Airflow container — run this checkpoint there:

    docker compose exec airflow-scheduler python /opt/project/checkpoints/run.py 7

Run via:  make checkpoint 7
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

DAG_ID = "weekly_procurement_etl"


def main() -> int:
    print("Checkpoint 7 — Airflow DAG")
    print("-" * 44)

    dag_file = REPO / "dags" / "weekly_procurement_etl.py"
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(dag_file)],
        capture_output=True,
        text=True,
        check=False,
    )
    syntax_ok = result.returncode == 0
    print(f"  {'✔' if syntax_ok else '✖'} DAG file compiles (syntax)")
    if not syntax_ok:
        print(result.stderr.strip())
        print("-" * 44)
        print("STATUS: FAILED")
        return 1

    if importlib.util.find_spec("airflow") is None:
        print(
            "  ! airflow not installed here — full parse runs in the Airflow container"
        )
        print("    docker compose up -d airflow-webserver airflow-scheduler")
        print("    docker compose exec airflow-scheduler airflow dags list")
        print("-" * 44)
        print("STATUS: FAILED")
        return 1

    from airflow.models import DagBag

    bag = DagBag(dag_folder=str(REPO / "dags"), include_examples=False)
    if bag.import_errors:
        print("  ✖ DagBag import errors:")
        for path, err in bag.import_errors.items():
            print(f"    {path}: {err.splitlines()[-1]}")
        print("-" * 44)
        print("STATUS: FAILED")
        return 1
    if DAG_ID not in bag.dags:
        print(f"  ✖ DAG '{DAG_ID}' not found")
        print("-" * 44)
        print("STATUS: FAILED")
        return 1

    print(f"  ✔ DAG '{DAG_ID}' parsed ({len(bag.dags[DAG_ID].tasks)} tasks)")
    print("-" * 44)
    print("STATUS: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
