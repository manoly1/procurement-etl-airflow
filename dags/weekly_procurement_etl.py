"""weekly_procurement_etl — the Airflow port of the Power Automate chain.

Schedule: Mondays at 09:00 (``0 9 * * 1``). Two source branches — Open PO and
All PRs — run independently: a failure in one branch stops only that branch,
not the other, mirroring the source-grouped fail-fast of the original PAD
chain. Each branch runs the same ETL core the CLI uses (generate -> snapshot ->
load), so nothing about the business logic is Airflow-specific.

Time semantics (data_interval / catchup / backfill) arrive in Module 8; here the
reporting week is a fixed default so the graph stays the focus.
"""

from __future__ import annotations

import os
import sys
import tempfile

import pendulum
from airflow.decorators import dag, task

# The repository is mounted into the container; make etl / datagen importable.
sys.path.insert(0, os.environ.get("PROJECT_ROOT", "/opt/project"))

DATASETS = ("open_po", "all_prs")
DEFAULT_WEEK = 29
RAW_DIR = os.environ.get("RAW_DIR", "/opt/project/data/raw")


@task
def wait_for_files() -> bool:
    """Placeholder gate. A real file sensor lands in Module 8."""
    os.makedirs(RAW_DIR, exist_ok=True)
    return True


@task
def generate(dataset: str, week: int = DEFAULT_WEEK) -> str:
    """Simulate the source extract arriving (datagen stands in for SAP)."""
    from datagen.generate import generate_file

    return generate_file(dataset, week, dirty_on=True, out_dir=RAW_DIR)


@task
def snapshot(dataset: str, path: str, week: int = DEFAULT_WEEK) -> str:
    """extract -> transform; persist the snapshot to a parquet file for handoff."""
    from datagen.seeds import build_seeds
    from etl.pipeline import build_snapshot_for

    frame = build_snapshot_for(dataset, path, week, seeds=build_seeds())
    out = os.path.join(tempfile.gettempdir(), f"{dataset}_W{week}.parquet")
    frame.to_parquet(out)
    return out


@task
def load(dataset: str, path: str) -> int:
    """Idempotent UPSERT of the snapshot into Postgres."""
    import pandas as pd

    from etl.load import get_engine, load_snapshot

    frame = pd.read_parquet(path)
    return load_snapshot(frame, dataset, get_engine())


@task
def notify(rows_per_dataset: list[int]) -> None:
    """Report the run. Real alerting (Telegram callbacks) comes in Module 8."""
    print(f"weekly_procurement_etl loaded rows: {rows_per_dataset}")


@dag(
    dag_id="weekly_procurement_etl",
    schedule="0 9 * * 1",
    start_date=pendulum.datetime(2026, 6, 22, tz="UTC"),
    catchup=False,
    default_args={"retries": 1},
    tags=["procurement", "etl"],
)
def weekly_procurement_etl():
    ready = wait_for_files()

    loaded = []
    for dataset in DATASETS:
        extracted = generate.override(task_id=f"generate_{dataset}")(dataset)
        snap = snapshot.override(task_id=f"snapshot_{dataset}")(dataset, extracted)
        rows = load.override(task_id=f"load_{dataset}")(dataset, snap)
        ready >> extracted  # gate both branches on the file check
        loaded.append(rows)

    notify(loaded)


dag_instance = weekly_procurement_etl()
