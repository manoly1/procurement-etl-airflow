"""S3-compatible object storage (MinIO) for the raw layer.

The weekly xlsx extracts land in an object store — a local stand-in for the
cloud data lake (S3 / GCS / ADLS) a production pipeline would use — instead of
living only on a local disk. ``boto3`` speaks the S3 API and MinIO implements
it, so the exact same code runs against MinIO locally and real S3 in the cloud.

Every knob comes from the environment (endpoint, keys, bucket) — never
hardcoded. That is the deliberate opposite of the old ``Config.bas`` with the
share path baked in.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from mypy_boto3_s3 import S3Client


def object_key(dataset: str, week: int, filename: str) -> str:
    """Partitioned object key for a weekly extract.

    Mirrors the on-disk Hive-style layout so the lake browses the same way:
    ``raw/dataset=open_po/week=29/open_po_W29.xlsx``. The partition prefix is
    what lets a query engine prune by dataset/week without reading every file.
    """
    return f"raw/dataset={dataset}/week={week}/{filename}"


@dataclass(frozen=True)
class StorageConfig:
    """Connection settings for the object store, sourced from the environment."""

    endpoint_url: str
    access_key: str
    secret_key: str
    bucket: str
    region: str = "us-east-1"

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> StorageConfig:
        """Build a config from ``MINIO_*`` / ``S3_*`` variables.

        Defaults match the docker-compose MinIO service so a fresh checkout
        works out of the box; secrets are still overridable per environment.
        """
        e = os.environ if env is None else env
        endpoint = e.get("MINIO_ENDPOINT") or e.get("S3_ENDPOINT_URL")
        return cls(
            endpoint_url=endpoint or "http://localhost:9000",
            access_key=e.get("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=e.get("MINIO_SECRET_KEY", "minioadmin"),
            bucket=e.get("MINIO_BUCKET", "procurement-raw"),
            region=e.get("AWS_REGION", "us-east-1"),
        )


class ObjectStore:
    """Thin wrapper over a boto3 S3 client scoped to one bucket.

    The client is created lazily so importing this module (and unit-testing the
    key helpers) never requires a live endpoint or even boto3 installed.
    """

    def __init__(self, config: StorageConfig | None = None) -> None:
        self.config = config or StorageConfig.from_env()
        self._client: S3Client | None = None

    @property
    def client(self) -> S3Client:
        if self._client is None:
            import boto3

            kwargs = {
                "aws_access_key_id": self.config.access_key,
                "aws_secret_access_key": self.config.secret_key,
                "region_name": self.config.region,
            }
            # Only override the endpoint for a self-hosted store (MinIO). Left
            # empty, boto3 targets real AWS S3 — same code, cloud or local.
            if self.config.endpoint_url:
                kwargs["endpoint_url"] = self.config.endpoint_url
            self._client = boto3.client("s3", **kwargs)
        return self._client

    def ensure_bucket(self) -> None:
        """Create the bucket if it does not exist yet (idempotent)."""
        from botocore.exceptions import ClientError

        try:
            self.client.head_bucket(Bucket=self.config.bucket)
        except ClientError:
            self.client.create_bucket(Bucket=self.config.bucket)

    def put_file(self, local_path: str | Path, key: str) -> str:
        """Upload a local file to ``key``; returns the key."""
        self.client.upload_file(str(local_path), self.config.bucket, key)
        return key

    def get_file(self, key: str, local_path: str | Path) -> Path:
        """Download ``key`` to ``local_path``; returns the local path."""
        dest = Path(local_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        self.client.download_file(self.config.bucket, key, str(dest))
        return dest

    def exists(self, key: str) -> bool:
        """True if an object with ``key`` is present in the bucket."""
        from botocore.exceptions import ClientError

        try:
            self.client.head_object(Bucket=self.config.bucket, Key=key)
        except ClientError:
            return False
        return True

    def list_prefix(self, prefix: str) -> list[str]:
        """All object keys under ``prefix`` (sorted)."""
        paginator = self.client.get_paginator("list_objects_v2")
        keys: list[str] = []
        for page in paginator.paginate(Bucket=self.config.bucket, Prefix=prefix):
            keys.extend(obj["Key"] for obj in page.get("Contents", []))
        return sorted(keys)


def land_extract(
    local_path: str | Path,
    dataset: str,
    week: int,
    store: ObjectStore | None = None,
) -> str:
    """Upload a weekly extract into the raw bucket under its partitioned key.

    This is the seam the CLI/DAG call to "land raw into the lake". Returns the
    object key so the caller can record where the snapshot came from.
    """
    store = store or ObjectStore()
    store.ensure_bucket()
    key = object_key(dataset, week, Path(local_path).name)
    return store.put_file(local_path, key)
