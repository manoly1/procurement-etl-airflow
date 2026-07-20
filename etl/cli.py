"""ETL core CLI — the headless entry point (the RunMacro.vbs analogue).

    python -m etl run --dataset open_po --week 29 --path <extract.xlsx>

The same `build_snapshot` + `load_snapshot` the Airflow DAG will call, runnable
by hand. Requires DATABASE_URL to be set (see .env.example).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import typer

from .load import get_engine, load_snapshot
from .pipeline import build_snapshot_for

app = typer.Typer(help="Run the ETL core.", no_args_is_help=True, add_completion=False)


def _load_rates(path: str) -> dict[str, pd.DataFrame] | None:
    """Load the rates seed for enrichment if the CSV exists."""
    csv = Path(path)
    return {"rates": pd.read_csv(csv)} if csv.exists() else None


@app.command()
def run(
    dataset: str = typer.Option(..., help="open_po | all_prs"),
    week: int = typer.Option(..., help="ISO week number"),
    path: str = typer.Option(..., help="Path to the extract xlsx"),
    rates: str = typer.Option("seeds/rates.csv", help="Rates seed CSV (optional)"),
    config_dir: str = typer.Option("config/datasets", help="Dataset config directory"),
) -> None:
    """Extract -> transform -> load one dataset/week into Postgres."""
    seeds = _load_rates(rates)
    snapshot = build_snapshot_for(
        dataset, path, week, seeds=seeds, config_dir=config_dir
    )
    engine = get_engine()
    rows = load_snapshot(snapshot, dataset, engine)
    typer.echo(f"loaded {rows} rows into raw.{dataset} (week {week})")


if __name__ == "__main__":
    app()
