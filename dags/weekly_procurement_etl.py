"""weekly_procurement_etl — the Airflow port of the Power Automate chain.

Schedule: Mondays at 09:00 (``0 9 * * 1``). The reporting week comes from the
run's **logical date** (``data_interval_start``), not the wall-clock day the job
runs — the same rule as ``ReportDate = Monday of the sheet's week``. That is what
makes ``airflow dags backfill`` replay past weeks correctly (the multi-week
``*_SelectedWeeks`` of the original project).

Two source branches (Open PO, All PRs) run independently with fail-fast, each:
``generate -> wait_for_file (sensor) -> land -> snapshot -> load``. The extract
lands in the MinIO object store (the data-lake raw layer) before it is
transformed. Failures alert to Telegram via the DAG callbacks; tasks retry
before they give up.
"""

from __future__ import annotations

import os
import sys
import tempfile
from datetime import timedelta

import pendulum
from airflow.decorators import dag, task
from airflow.operators.python import get_current_context

# The repository is mounted into the container; make etl / datagen importable.
sys.path.insert(0, os.environ.get("PROJECT_ROOT", "/opt/project"))

DATASETS = ("open_po", "all_prs")
RAW_DIR = os.environ.get("RAW_DIR", "/opt/project/data/raw")


def _extract_path(dataset: str, week: int) -> str:
    return os.path.join(
        RAW_DIR, dataset, f"week={week:02d}", f"{dataset}_W{week:02d}.xlsx"
    )


# --- alerting callbacks (Teams-notification analogue) ------------------------
def _on_failure(context) -> None:
    from etl.notify import build_message, telegram_notify

    telegram_notify(
        build_message(context["dag"].dag_id, "failed", context.get("run_id"))
    )


def _on_success(context) -> None:
    from etl.notify import build_message, telegram_notify

    telegram_notify(
        build_message(context["dag"].dag_id, "success", context.get("run_id"))
    )


# --- tasks -------------------------------------------------------------------
@task
def resolve_week() -> int:
    """The reporting week is the ISO week of the run's logical date."""
    from etl.dates import week_from_logical_date

    context = get_current_context()
    return week_from_logical_date(context["data_interval_start"])


@task
def generate(dataset: str, week: int) -> str:
    """Simulate the source extract arriving (datagen stands in for SAP)."""
    from datagen.generate import generate_file

    return generate_file(dataset, week, dirty_on=True, out_dir=RAW_DIR)


@task.sensor(poke_interval=15, timeout=300, mode="poke")
def wait_for_file(dataset: str, week: int) -> bool:
    """Wait for the week's file to appear — the DE version of a PAD file trigger."""
    path = _extract_path(dataset, week)
    return os.path.exists(path)


@task
def land(dataset: str, path: str, week: int) -> str:
    """Land the raw extract into the object store — the data-lake raw layer."""
    from etl.storage import land_extract

    return land_extract(path, dataset, week)


@task
def snapshot(dataset: str, path: str, week: int) -> str:
    """extract -> transform; persist the snapshot to parquet for handoff."""
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

    return load_snapshot(pd.read_parquet(path), dataset, get_engine())


@dag(
    dag_id="weekly_procurement_etl",
    schedule="0 9 * * 1",
    start_date=pendulum.datetime(2026, 6, 22, tz="UTC"),
    catchup=False,  # backfill on demand instead of replaying everything on deploy
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    on_failure_callback=_on_failure,
    on_success_callback=_on_success,
    tags=["procurement", "etl"],
)
def weekly_procurement_etl():
    week = resolve_week()

    for dataset in DATASETS:
        extracted = generate.override(task_id=f"generate_{dataset}")(dataset, week)
        sensed = wait_for_file.override(task_id=f"wait_{dataset}")(dataset, week)
        landed = land.override(task_id=f"land_{dataset}")(dataset, extracted, week)
        snap = snapshot.override(task_id=f"snapshot_{dataset}")(
            dataset, extracted, week
        )
        load.override(task_id=f"load_{dataset}")(dataset, snap)
        extracted >> sensed >> landed >> snap


dag_instance = weekly_procurement_etl()
