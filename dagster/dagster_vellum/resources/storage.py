"""Dagster resources — document storage (PVC or S3)."""
from __future__ import annotations

import os
from pathlib import Path

from dagster import ConfigurableResource


class LocalDocumentStorageResource(ConfigurableResource):
    """Read documents from a local PVC-mounted directory."""

    document_path: str = "/data/documents"

    def list_files(self) -> list[str]:
        base = Path(self.document_path)
        if not base.exists():
            return []
        return [str(f) for f in base.iterdir() if f.is_file()]

    def read_bytes(self, filepath: str) -> bytes:
        return Path(filepath).read_bytes()


class S3DocumentStorageResource(ConfigurableResource):
    """Read documents from an S3-compatible bucket via boto3."""

    bucket: str
    endpoint_url: str = ""
    access_key: str = ""
    secret_key: str = ""

    def _client(self):
        import boto3  # type: ignore[import-untyped]

        return boto3.client(
            "s3",
            endpoint_url=self.endpoint_url or None,
            aws_access_key_id=self.access_key or None,
            aws_secret_access_key=self.secret_key or None,
        )

    def list_files(self) -> list[str]:
        response = self._client().list_objects_v2(Bucket=self.bucket)
        return [obj["Key"] for obj in response.get("Contents", [])]

    def read_bytes(self, key: str) -> bytes:
        response = self._client().get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()


def make_storage_resource() -> LocalDocumentStorageResource | S3DocumentStorageResource:
    """Factory: reads USE_S3_STORAGE env var and returns the appropriate resource."""
    if os.getenv("USE_S3_STORAGE", "false").lower() == "true":
        return S3DocumentStorageResource(
            bucket=os.getenv("S3_BUCKET", "vellum-documents"),
            endpoint_url=os.getenv("S3_ENDPOINT", ""),
            access_key=os.getenv("S3_ACCESS_KEY", ""),
            secret_key=os.getenv("S3_SECRET_KEY", ""),
        )
    return LocalDocumentStorageResource(
        document_path=os.getenv("DOCUMENT_STORAGE_PATH", "/data/documents")
    )
