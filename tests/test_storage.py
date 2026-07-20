"""Tests for the object-storage (MinIO/S3) raw layer.

The key helpers are pure and always run. The round-trip against a bucket uses
``moto`` to mock S3 in-process (no MinIO, no network); it skips cleanly if moto
is not installed so the suite stays green on a minimal checkout.
"""

from __future__ import annotations

import pytest

from etl.storage import ObjectStore, StorageConfig, land_extract, object_key

# --- pure helpers -------------------------------------------------------------


def test_object_key_is_hive_partitioned() -> None:
    key = object_key("open_po", 29, "open_po_W29.xlsx")
    assert key == "raw/dataset=open_po/week=29/open_po_W29.xlsx"


def test_object_key_uses_only_the_basename() -> None:
    # A full path in must not leak directories into the object key.
    key = object_key("all_prs", 5, "all_prs_W5.xlsx")
    assert key.startswith("raw/dataset=all_prs/week=5/")
    assert "/" not in key.rsplit("/", 1)[-1].replace("all_prs_W5.xlsx", "")


def test_config_from_env_reads_minio_vars() -> None:
    cfg = StorageConfig.from_env(
        {
            "MINIO_ENDPOINT": "http://minio:9000",
            "MINIO_ACCESS_KEY": "key",
            "MINIO_SECRET_KEY": "secret",
            "MINIO_BUCKET": "bucket-x",
        }
    )
    assert cfg.endpoint_url == "http://minio:9000"
    assert cfg.access_key == "key"
    assert cfg.bucket == "bucket-x"


def test_config_from_env_defaults() -> None:
    cfg = StorageConfig.from_env({})
    assert cfg.endpoint_url == "http://localhost:9000"
    assert cfg.bucket == "procurement-raw"


# --- round-trip against a mocked bucket ---------------------------------------


@pytest.fixture
def mock_s3():
    # moto mocks S3 in-process; skip the round-trip if it is not installed.
    moto = pytest.importorskip("moto")

    with moto.mock_aws():
        yield


@pytest.fixture
def store(mock_s3) -> ObjectStore:
    # Empty endpoint -> boto3 default AWS endpoint, which moto intercepts.
    cfg = StorageConfig(
        endpoint_url="",
        access_key="test",
        secret_key="test",
        bucket="procurement-raw-test",
    )
    s = ObjectStore(cfg)
    s.ensure_bucket()
    return s


def test_put_get_round_trip(store, tmp_path) -> None:
    src = tmp_path / "open_po_W29.xlsx"
    src.write_bytes(b"binary-extract-payload")

    key = object_key("open_po", 29, src.name)
    store.put_file(src, key)

    assert store.exists(key) is True
    out = store.get_file(key, tmp_path / "downloaded.xlsx")
    assert out.read_bytes() == b"binary-extract-payload"


def test_exists_false_for_missing_key(store) -> None:
    assert store.exists("raw/dataset=nope/week=1/missing.xlsx") is False


def test_list_prefix_returns_sorted_keys(store, tmp_path) -> None:
    for wk in (30, 29):
        f = tmp_path / f"open_po_W{wk}.xlsx"
        f.write_bytes(b"x")
        store.put_file(f, object_key("open_po", wk, f.name))

    keys = store.list_prefix("raw/dataset=open_po/")
    assert keys == sorted(keys)
    assert len(keys) == 2


def test_land_extract_lands_under_partition(store, tmp_path) -> None:
    src = tmp_path / "all_prs_W5.xlsx"
    src.write_bytes(b"payload")

    key = land_extract(src, "all_prs", 5, store=store)

    assert key == "raw/dataset=all_prs/week=5/all_prs_W5.xlsx"
    assert store.exists(key) is True
