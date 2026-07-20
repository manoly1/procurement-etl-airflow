"""Core pipeline entry: extract -> transform -> weekly snapshot.

This is the seam the CLI and the Airflow DAG both call. Keeping it here means the
same code produces a snapshot whether a human or the scheduler triggered it —
the RunMacro.vbs / *_Headless split, done right.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .column_resolver import DatasetConfig, load_dataset_config
from .extract import read_extract
from .transform import transform


def build_snapshot(
    path: str | Path,
    config: DatasetConfig,
    week: int,
    seeds: dict[str, pd.DataFrame] | None = None,
) -> pd.DataFrame:
    """Read an extract file and return the clean weekly snapshot."""
    raw = read_extract(path, config)
    return transform(raw, config, week, seeds)


def build_snapshot_for(
    dataset: str,
    path: str | Path,
    week: int,
    seeds: dict[str, pd.DataFrame] | None = None,
    config_dir: str | Path = "config/datasets",
) -> pd.DataFrame:
    """Convenience wrapper that loads the dataset config by name first."""
    config = load_dataset_config(dataset, config_dir)
    return build_snapshot(path, config, week, seeds)
