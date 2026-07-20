#!/usr/bin/env python3
"""Checkpoint 2 — Python & pandas katas.

Runs the test suite (the NormalizeKey / CompactRowsByKey helpers rewritten in
Python) and reports the STATUS contract based on pytest's result. This is the
"green tests" gate for Module 2.

Run via:  make checkpoint 2
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def main() -> int:
    print("Checkpoint 2 — Python & pandas katas")
    print("-" * 44)

    if importlib.util.find_spec("pytest") is None:
        print('  ✖ pytest not installed (run: pip install -e ".[dev]")')
        print("-" * 44)
        print("STATUS: FAILED")
        return 1
    if importlib.util.find_spec("pandas") is None:
        print('  ✖ pandas not installed (run: pip install -e ".")')
        print("-" * 44)
        print("STATUS: FAILED")
        return 1

    # Inherit stdout/stderr so the learner sees the full pytest report.
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/"],
        cwd=REPO,
        check=False,
    )
    ok = proc.returncode == 0

    print("-" * 44)
    print("STATUS: PASSED" if ok else "STATUS: FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
