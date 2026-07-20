"""Tests for etl.extract and etl.column_resolver, on real datagen files."""

from __future__ import annotations

import pytest

from datagen.generate import generate_file
from etl.column_resolver import (
    ColumnResolutionError,
    load_dataset_config,
    resolve_columns,
)
from etl.extract import find_header_row, read_extract, read_raw


def test_load_config_has_headers_and_aliases() -> None:
    cfg = load_dataset_config("open_po")
    assert cfg.name == "open_po"
    assert cfg.key == ("po_number", "po_item")
    known = cfg.known_headers()
    assert "PO Number" in known
    assert "PO No" in known  # alias


def test_find_header_row_on_dirty_file(tmp_path) -> None:
    cfg = load_dataset_config("open_po")
    path = generate_file("open_po", 29, dirty_on=True, out_dir=str(tmp_path))
    raw = read_raw(path)
    # dirty file: row 0 is the report-date title, row 1 the real headers
    assert find_header_row(raw, cfg.known_headers()) == 1


def test_find_header_row_on_clean_file(tmp_path) -> None:
    cfg = load_dataset_config("all_prs")
    path = generate_file("all_prs", 25, dirty_on=False, out_dir=str(tmp_path))
    raw = read_raw(path)
    assert find_header_row(raw, cfg.known_headers()) == 0


def test_read_extract_returns_canonical_columns(tmp_path) -> None:
    cfg = load_dataset_config("open_po")
    path = generate_file("open_po", 29, dirty_on=True, out_dir=str(tmp_path))
    df = read_extract(path, cfg)
    assert "po_number" in df.columns
    assert "material" in df.columns
    assert "PO Number" not in df.columns  # renamed to canonical


def test_read_extract_drops_junk_rows(tmp_path) -> None:
    cfg = load_dataset_config("open_po")
    path = generate_file("open_po", 29, dirty_on=True, out_dir=str(tmp_path))
    df = read_extract(path, cfg)
    assert not df.isin(["Total", "*** End of report ***"]).any().any()
    assert len(df) >= 60  # 60 rows + duplicates, minus junk


def test_resolver_uses_aliases() -> None:
    cfg = load_dataset_config("open_po")
    cols = ["PO No", "Item", "Material", "Vendor", "Qty", "Price"]
    res = resolve_columns(cols, cfg)
    assert res.mapping["po_number"] == "PO No"
    assert res.mapping["supplier"] == "Vendor"
    assert res.mapping["order_quantity"] == "Qty"


def test_resolver_missing_required_raises_with_message() -> None:
    cfg = load_dataset_config("open_po")
    with pytest.raises(ColumnResolutionError) as exc:
        resolve_columns(["PO Number", "PO Item"], cfg)  # no Material
    assert "material" in str(exc.value)
    assert "Available columns" in str(exc.value)


def test_resolver_skips_absent_optional() -> None:
    cfg = load_dataset_config("open_po")
    cols = [
        "PO Number",
        "PO Item",
        "Material",
        "Supplier",
        "Order Quantity",
        "Net Price",
    ]
    res = resolve_columns(cols, cfg)
    assert "currency" in res.missing_optional
    assert "po_number" in res.mapping
