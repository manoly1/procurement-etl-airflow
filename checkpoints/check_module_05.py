#!/usr/bin/env python3
"""Checkpoint 5 — weekly snapshot transform.

Builds the W29 snapshot for both datasets and confirms the transform invariants:
keys are unique (dedup worked), the result is deterministic, and ReportWeek is
stamped.

Run via:  make checkpoint 5
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))


def main() -> int:
    print("Checkpoint 5 — weekly snapshot transform")
    print("-" * 44)

    for mod in ("pandas", "openpyxl", "yaml", "faker"):
        if importlib.util.find_spec(mod) is None:
            print(f'  ✖ {mod} not installed (run: pip install -e ".[dev]")')
            print("-" * 44)
            print("STATUS: FAILED")
            return 1

    from datagen.generate import generate_file
    from datagen.seeds import build_seeds
    from etl.pipeline import build_snapshot_for

    config_dir = str(REPO / "config" / "datasets")
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        for name in ("open_po", "all_prs"):
            path = generate_file(name, 29, dirty_on=True, out_dir=tmp)
            first = build_snapshot_for(
                name, path, 29, seeds=build_seeds(), config_dir=config_dir
            )
            again = build_snapshot_for(
                name, path, 29, seeds=build_seeds(), config_dir=config_dir
            )
            unique = bool(first["key"].is_unique)
            deterministic = first.equals(again)
            stamped = bool((first["report_week"] == 29).all())
            good = unique and deterministic and stamped and len(first) > 40
            ok = ok and good
            glyph = "✔" if good else "✖"
            print(f"  {glyph} {name}: {len(first)} rows, unique+deterministic+stamped")

    print("-" * 44)
    print("STATUS: PASSED" if ok else "STATUS: FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
