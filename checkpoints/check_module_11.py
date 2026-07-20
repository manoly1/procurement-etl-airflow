#!/usr/bin/env python3
"""Checkpoint 11 — the object-storage (MinIO) raw layer.

Validates the storage layer without a live endpoint: the partitioned object
key is correct, config reads from the environment, and a full put/get/exists
round-trip works against an in-process mock (moto) when it is installed. The
end-to-end gate — landing into a real MinIO bucket — runs via `make up` and
the `land` CLI on your machine.

Run via:  make checkpoint 11
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))


def main() -> int:
    print("Checkpoint 11 — object storage (MinIO) raw layer")
    print("-" * 48)

    if importlib.util.find_spec("boto3") is None:
        print('  ✖ boto3 not installed (run: pip install -e ".")')
        print("-" * 48)
        print("STATUS: FAILED")
        return 1
    print("  ✔ boto3 available (S3 API client)")

    from etl.storage import ObjectStore, StorageConfig, land_extract, object_key

    # 1. Partitioned key layout.
    key = object_key("open_po", 29, "open_po_W29.xlsx")
    key_ok = key == "raw/dataset=open_po/week=29/open_po_W29.xlsx"
    print(f"  {'✔' if key_ok else '✖'} object key: {key}")

    # 2. Config reads from the environment.
    cfg = StorageConfig.from_env(
        {"MINIO_ENDPOINT": "http://minio:9000", "MINIO_BUCKET": "b"}
    )
    cfg_ok = cfg.endpoint_url == "http://minio:9000" and cfg.bucket == "b"
    print(f"  {'✔' if cfg_ok else '✖'} config from env (endpoint + bucket)")

    # 3. Full round-trip against a mocked bucket, if moto is installed.
    round_trip_ok = True
    if importlib.util.find_spec("moto") is None:
        print("  … moto not installed — skipping mock round-trip")
        print("      (run `make up` + `python -m etl land ...` against real MinIO)")
    else:
        import tempfile

        from moto import mock_aws

        with mock_aws():
            store = ObjectStore(
                StorageConfig("", "test", "test", "chk-bucket"),
            )
            store.ensure_bucket()
            with tempfile.TemporaryDirectory() as tmp:
                src = Path(tmp) / "open_po_W29.xlsx"
                src.write_bytes(b"payload")
                landed = land_extract(src, "open_po", 29, store=store)
                back = store.get_file(landed, Path(tmp) / "out.xlsx")
                round_trip_ok = (
                    store.exists(landed)
                    and back.read_bytes() == b"payload"
                    and landed == "raw/dataset=open_po/week=29/open_po_W29.xlsx"
                )
        marker = "✔" if round_trip_ok else "✖"
        print(f"  {marker} put/get/exists round-trip (mocked S3)")

    ok = key_ok and cfg_ok and round_trip_ok
    print("-" * 48)
    print("STATUS: PASSED" if ok else "STATUS: FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
