#!/usr/bin/env python3
"""Checkpoint 3 — synthetic data generator.

Generates weeks W25-W30 of both datasets to a temp dir and confirms the dirty
flag actually changes the output. Reports the STATUS contract for Module 3.

Run via:  make checkpoint 3
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))  # make the project packages importable


def main() -> int:
    print("Checkpoint 3 — synthetic data generator")
    print("-" * 44)

    for mod in ("pandas", "openpyxl", "faker", "typer"):
        if importlib.util.find_spec(mod) is None:
            print(f'  ✖ {mod} not installed (run: pip install -e ".[dev]")')
            print("-" * 44)
            print("STATUS: FAILED")
            return 1

    from datagen.datasets import DATASETS
    from datagen.generate import generate_file, generate_frame

    weeks = range(25, 31)
    with tempfile.TemporaryDirectory() as tmp:
        for name in DATASETS:
            for wk in weeks:
                generate_file(name, wk, dirty_on=True, out_dir=tmp)
        n_files = sum(1 for _ in Path(tmp).rglob("*.xlsx"))

    expected = len(DATASETS) * len(list(weeks))
    files_ok = n_files == expected
    glyph = "✔" if files_ok else "✖"
    print(f"  {glyph} generated {n_files}/{expected} files (W25-W30, both datasets)")

    dirty_df, _ = generate_frame("open_po", 29, dirty_on=True, seed=1)
    clean_df, _ = generate_frame("open_po", 29, dirty_on=False, seed=1)
    toggle_ok = dirty_df.shape != clean_df.shape or not dirty_df.equals(clean_df)
    print(f"  {'✔' if toggle_ok else '✖'} dirty/clean flag changes the output")

    ok = files_ok and toggle_ok
    print("-" * 44)
    print("STATUS: PASSED" if ok else "STATUS: FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
