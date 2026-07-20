#!/usr/bin/env python3
"""Checkpoint 9 — tests & data quality.

Runs the test suite (unit + dirty-data fixtures) and confirms a quality check
catches a poisoned frame — the "bad data is caught before marts" gate.

Run via:  make checkpoint 9
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))


def main() -> int:
    print("Checkpoint 9 — tests & data quality")
    print("-" * 44)

    for mod in ("pandas", "pytest", "faker", "yaml", "openpyxl"):
        if importlib.util.find_spec(mod) is None:
            print(f'  ✖ {mod} not installed (run: pip install -e ".[dev]")')
            print("-" * 44)
            print("STATUS: FAILED")
            return 1

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    tests_ok = proc.returncode == 0
    summary = (
        proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "no output"
    )
    print(f"  {'✔' if tests_ok else '✖'} test suite: {summary}")

    import pandas as pd

    from datagen.generate import generate_file
    from datagen.seeds import build_seeds
    from etl.pipeline import build_snapshot_for
    from etl.quality import QualityError, unique_keys

    with tempfile.TemporaryDirectory() as tmp:
        path = generate_file("open_po", 29, dirty_on=True, out_dir=tmp)
        snap = build_snapshot_for("open_po", path, 29, seeds=build_seeds())
        poisoned = pd.concat([snap, snap.iloc[[0]]], ignore_index=True)
        try:
            unique_keys(poisoned, ["key"])
            caught = False
        except QualityError:
            caught = True
    print(f"  {'✔' if caught else '✖'} data-quality catches a duplicate-key frame")

    ok = tests_ok and caught
    print("-" * 44)
    print("STATUS: PASSED" if ok else "STATUS: FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
