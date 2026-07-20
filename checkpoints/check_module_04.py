#!/usr/bin/env python3
"""Checkpoint 4 — extract & column mapping.

Generates dirty W29 extracts for both datasets, reads them through the header
detection + junk removal + column resolver, and confirms canonical key columns
are present and junk rows are gone.

Run via:  make checkpoint 4
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))


def main() -> int:
    print("Checkpoint 4 — extract & column mapping")
    print("-" * 44)

    for mod in ("pandas", "openpyxl", "yaml", "faker"):
        if importlib.util.find_spec(mod) is None:
            print(f'  ✖ {mod} not installed (run: pip install -e ".[dev]")')
            print("-" * 44)
            print("STATUS: FAILED")
            return 1

    from datagen.generate import generate_file
    from etl.column_resolver import load_dataset_config
    from etl.extract import read_extract

    config_dir = str(REPO / "config" / "datasets")
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        for name in ("open_po", "all_prs"):
            cfg = load_dataset_config(name, config_dir)
            path = generate_file(name, 29, dirty_on=True, out_dir=tmp)
            df = read_extract(path, cfg)
            keys_present = all(k in df.columns for k in cfg.key)
            junk_gone = not df.isin(["Total", "*** End of report ***"]).any().any()
            good = keys_present and junk_gone and len(df) >= 50
            ok = ok and good
            glyph = "✔" if good else "✖"
            print(f"  {glyph} {name}: {len(df)} rows, keys present, junk removed")

    print("-" * 44)
    print("STATUS: PASSED" if ok else "STATUS: FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
