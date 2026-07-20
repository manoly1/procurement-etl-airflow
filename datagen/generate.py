"""Core generation: build a clean frame, dirty it, write an xlsx extract."""

from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker
from openpyxl import Workbook

from . import dirty
from .datasets import DATASETS, Dataset

YEAR = 2026
CURRENCIES = ("EUR", "USD", "GBP", "PLN")
PLANTS = ("P100", "P200", "P300")


def report_monday(week: int, year: int = YEAR) -> date:
    """Monday of the given ISO week — the snapshot's logical date (ReportDate)."""
    return date.fromisocalendar(year, week, 1)


def _build_records(
    ds: Dataset,
    week: int,
    n_rows: int,
    rng: random.Random,
    suppliers: list[str],
    people: list[str],
) -> list[dict]:
    monday = report_monday(week)
    records: list[dict] = []
    for i in range(n_rows):
        material = rng.randint(100000, 9999999)
        due = monday + timedelta(days=rng.randint(0, 30))
        common = {
            "Material": material,
            "Material Description": f"Spare part {rng.randint(1, 9999)}",
            "Plant": rng.choice(PLANTS),
        }
        if ds.name == "open_po":
            rec = {
                "PO Number": f"45{rng.randint(0, 9999999):07d}",
                "PO Item": (i % 8 + 1) * 10,
                **common,
                "Supplier": rng.choice(suppliers),
                "Order Quantity": rng.randint(1, 500),
                "Net Price": round(rng.uniform(1, 5000), 2),
                "Currency": rng.choice(CURRENCIES),
                "Delivery Date": due.isoformat(),
                "Requisitioner": rng.choice(people),
            }
        else:
            rec = {
                "PR Number": f"10{rng.randint(0, 9999999):07d}",
                "PR Item": (i % 8 + 1) * 10,
                **common,
                "Requested Quantity": rng.randint(1, 500),
                "Requisitioner": rng.choice(people),
                "Responsible": rng.choice(people),
                "Release Date": due.isoformat(),
            }
        records.append({c: rec[c] for c in ds.columns})
    return records


def generate_frame(
    dataset: str,
    week: int,
    dirty_on: bool = True,
    seed: int | None = None,
    n_rows: int = 60,
) -> tuple[pd.DataFrame, set[str]]:
    """Build a (possibly dirty) DataFrame for one dataset/week, deterministically."""
    if dataset not in DATASETS:
        raise ValueError(
            f"unknown dataset {dataset!r}; expected one of {list(DATASETS)}"
        )
    ds = DATASETS[dataset]
    resolved_seed = seed if seed is not None else 20260000 + week
    rng = random.Random(resolved_seed)
    fake = Faker("en_US")
    fake.seed_instance(resolved_seed)

    suppliers = [fake.unique.company() for _ in range(15)]
    people = [fake.unique.name() for _ in range(10)]

    df = pd.DataFrame(
        _build_records(ds, week, n_rows, rng, suppliers, people),
        columns=list(ds.columns),
    )
    flags = dirty.default_flags(dirty_on)
    df = dirty.apply(df, ds, flags, rng)
    return df, flags


def _cell(value: object) -> object:
    """Normalize a cell for openpyxl: pandas NaN / None -> blank."""
    if value is None:
        return None
    if isinstance(value, float) and value != value:  # NaN
        return None
    return value


def write_xlsx(
    df: pd.DataFrame, path: str | Path, date_row1: str | None = None
) -> None:
    """Write the frame to xlsx, optionally with a title row above the headers."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    if date_row1:
        ws.append([f"Report Date: {date_row1}"])  # headers then land on row 2
    ws.append(list(df.columns))
    for row in df.itertuples(index=False, name=None):
        ws.append([_cell(v) for v in row])
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def generate_file(
    dataset: str,
    week: int,
    dirty_on: bool = True,
    out_dir: str = "data/raw",
    seed: int | None = None,
) -> str:
    """Generate one extract file and return its path.

    Files are partitioned like a data lake: ``<dataset>/week=NN/<dataset>_WNN.xlsx``.
    """
    df, flags = generate_frame(dataset, week, dirty_on, seed)
    date_row1 = report_monday(week).isoformat() if "date_in_row1" in flags else None
    out = Path(out_dir) / dataset / f"week={week:02d}"
    path = out / f"{dataset}_W{week:02d}.xlsx"
    write_xlsx(df, path, date_row1=date_row1)
    return str(path)
