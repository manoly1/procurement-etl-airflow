"""Tests for the transform layer, on real datagen files (extract -> transform)."""

from __future__ import annotations

import pandas as pd

from datagen.generate import generate_file
from datagen.seeds import build_seeds
from etl.column_resolver import load_dataset_config
from etl.dates import report_monday
from etl.extract import read_extract
from etl.pipeline import build_snapshot_for
from etl.transform import to_numeric, transform


def test_to_numeric_parses_messy_values() -> None:
    out = to_numeric(pd.Series(["1 234,50", "999,00", "42", None, 1234.5])).tolist()
    assert out[0] == 1234.5
    assert out[1] == 999.0
    assert out[2] == 42.0
    assert pd.isna(out[3])
    assert out[4] == 1234.5


def test_report_monday_week_29() -> None:
    assert report_monday(29).isoformat() == "2026-07-13"


def test_snapshot_numbers_are_numeric(tmp_path) -> None:
    path = generate_file("open_po", 29, dirty_on=True, out_dir=str(tmp_path))
    snap = build_snapshot_for("open_po", path, 29, seeds=build_seeds())
    assert pd.api.types.is_numeric_dtype(snap["net_price"])
    assert pd.api.types.is_numeric_dtype(snap["order_quantity"])


def test_snapshot_keys_are_unique(tmp_path) -> None:
    path = generate_file("open_po", 29, dirty_on=True, out_dir=str(tmp_path))
    snap = build_snapshot_for("open_po", path, 29)
    assert snap["key"].is_unique  # duplicate rows collapsed


def test_snapshot_drops_incomplete_keys(tmp_path) -> None:
    path = generate_file("open_po", 29, dirty_on=True, out_dir=str(tmp_path))
    cfg = load_dataset_config("open_po")
    snap = transform(read_extract(path, cfg), cfg, 29)
    assert not snap["key"].str.startswith("|").any()
    assert not snap["key"].str.endswith("|").any()


def test_snapshot_stamps_report_date(tmp_path) -> None:
    path = generate_file("all_prs", 25, dirty_on=True, out_dir=str(tmp_path))
    snap = build_snapshot_for("all_prs", path, 25)
    assert (snap["report_week"] == 25).all()
    assert (snap["report_date"] == report_monday(25).isoformat()).all()


def test_material_leading_zeros_preserved(tmp_path) -> None:
    path = generate_file("open_po", 29, dirty_on=True, out_dir=str(tmp_path))
    snap = build_snapshot_for("open_po", path, 29)
    assert (snap["material"].str.len() == 8).all()
    assert snap["material"].str.match(r"^\d{8}$").all()


def test_enrichment_adds_rate_and_line_value(tmp_path) -> None:
    path = generate_file("open_po", 29, dirty_on=True, out_dir=str(tmp_path))
    snap = build_snapshot_for("open_po", path, 29, seeds=build_seeds())
    assert "rate_to_eur" in snap.columns
    assert "line_value_eur" in snap.columns
    row = snap.iloc[0]
    expected = row["order_quantity"] * row["net_price"] * row["rate_to_eur"]
    assert abs(row["line_value_eur"] - expected) < 1e-6


def test_snapshot_is_deterministic(tmp_path) -> None:
    path = generate_file("open_po", 29, dirty_on=True, out_dir=str(tmp_path))
    a = build_snapshot_for("open_po", path, 29, seeds=build_seeds())
    b = build_snapshot_for("open_po", path, 29, seeds=build_seeds())
    pd.testing.assert_frame_equal(a, b)
