#!/usr/bin/env python3
"""Dispatcher for `make checkpoint N`.

Loads checkpoints/check_module_NN.py and calls its main(), which prints a
per-line report ending in `STATUS: PASSED` or `STATUS: FAILED` and returns a
process exit code (0 = passed). This mirrors the STATUS contract of the
original VBA Logger.bas: either everything is green, or it is visible which
line is red.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: python checkpoints/run.py N   (e.g. `make checkpoint 0`)")
        return 2

    raw = argv[0]
    try:
        num = int(raw)
    except ValueError:
        print(f"checkpoint id must be an integer, got {raw!r}")
        return 2

    script = Path(__file__).parent / f"check_module_{num:02d}.py"
    if not script.exists():
        print(f"no checkpoint script yet for module {num:02d} (expected {script.name})")
        return 2

    spec = importlib.util.spec_from_file_location(script.stem, script)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
