"""Smoke tests for the Stage-0 skeleton.

These just prove the skeleton is wired up and importable. Real coverage
(dirty-data fixtures, transforms, idempotency) arrives from Stage 1 onward.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_source_packages_import() -> None:
    import datagen  # noqa: F401
    import etl  # noqa: F401
    import etl.transform  # noqa: F401


def test_checkpoint_00_exposes_main() -> None:
    path = REPO / "checkpoints" / "check_module_00.py"
    assert path.exists(), "checkpoint 0 script is missing"
    spec = importlib.util.spec_from_file_location("check_module_00", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "checkpoint must expose a callable main()"
