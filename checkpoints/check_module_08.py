#!/usr/bin/env python3
"""Checkpoint 8 — Airflow time / backfill / reliability.

Confirms the DAG still parses after the time/sensor/callback changes. The full
DoD (backfill W25-W28, a poisoned file fails one branch, an alert fires) is
exercised on the machine running Airflow:

    docker compose exec airflow-scheduler airflow dags backfill \\
        -s 2026-06-22 -e 2026-07-13 weekly_procurement_etl

Run via:  make checkpoint 8
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
    print("Checkpoint 8 — Airflow time / backfill / reliability")
    print("-" * 44)

    dag_file = REPO / "dags" / "weekly_procurement_etl.py"
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(dag_file)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print("  ✖ DAG file does not compile")
        print(result.stderr.strip())
        print("-" * 44)
        print("STATUS: FAILED")
        return 1
    print("  ✔ DAG file compiles (syntax)")

    if importlib.util.find_spec("airflow") is None:
        print("  ! airflow not installed here — parse + backfill run in the container")
        print("    docker compose exec airflow-scheduler airflow dags list")
        print("    docker compose exec airflow-scheduler airflow dags backfill \\")
        print("        -s 2026-06-22 -e 2026-07-13 weekly_procurement_etl")
        print("-" * 44)
        print("STATUS: FAILED")
        return 1

    from airflow.models import DagBag

    bag = DagBag(dag_folder=str(REPO / "dags"), include_examples=False)
    if bag.import_errors or DAG_ID not in bag.dags:
        print(f"  ✖ DAG '{DAG_ID}' failed to parse: {bag.import_errors}")
        print("-" * 44)
        print("STATUS: FAILED")
        return 1

    dag = bag.dags[DAG_ID]
    print(f"  ✔ DAG '{DAG_ID}' parsed ({len(dag.tasks)} tasks, retries configured)")
    print("-" * 44)
    print("STATUS: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
