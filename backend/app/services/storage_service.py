"""Storage service — unified document storage interface.

Provides a consistent API for reading/writing documents regardless of backend:
  - Local: reads/writes to DOCUMENT_STORAGE_PATH (a PVC volume mount in K8s, or
    a local directory in hybrid dev mode).
  - S3: delegates to boto3 for any S3-compatible bucket (AWS S3, MinIO, Ceph).

Select the backend via the USE_S3_STORAGE env toggle. Defaults to local.
"""

import asyncio
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import AsyncGenerator

import aiofiles

from app.core.config import settings
from app.core.logging import logger


class StorageService(ABC):
    """Abstract interface for document storage — local PVC or cloud S3."""

    @abstractmethod
    async def upload(self, filename: str, src_path: str) -> None:
        """Copy a local file at *src_path* into the document store as *filename*."""
        ...

    @abstractmethod
    async def download(self, filename: str) -> AsyncGenerator[bytes, None]:
        """Stream the bytes of *filename* from the document store."""
        ...

    @abstractmethod
    async def list_files(self) -> list[str]:
        """Return a list of all document filenames visible in the store."""
        ...


class LocalStorageService(StorageService):
    """Read/write to DOCUMENT_STORAGE_PATH (a PVC volume mount or local directory)."""

    def __init__(self) -> None:
        self.base_path = Path(settings.DOCUMENT_STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload(self, filename: str, src_path: str) -> None:
        dest = self.base_path / filename
        await asyncio.to_thread(shutil.copy2, src_path, dest)
        logger.info("local_storage_uploaded", filename=filename, dest=str(dest))

    async def download(self, filename: str) -> AsyncGenerator[bytes, None]:
        path = self.base_path / filename
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {filename}")
        async with aiofiles.open(path, "rb") as fh:
            while chunk := await fh.read(32 * 1024):
                yield chunk

    async def list_files(self) -> list[str]:
        return [f.name for f in self.base_path.iterdir() if f.is_file()]


class S3StorageService(StorageService):
    """Read/write to an S3-compatible bucket via boto3."""

    def __init__(self) -> None:
        import boto3  # type: ignore[import-untyped]

        self.bucket = settings.S3_BUCKET
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT or None,
            aws_access_key_id=settings.S3_ACCESS_KEY or None,
            aws_secret_access_key=settings.S3_SECRET_KEY or None,
        )

    async def upload(self, filename: str, src_path: str) -> None:
        await asyncio.to_thread(self._client.upload_file, src_path, self.bucket, filename)
        logger.info("s3_storage_uploaded", filename=filename, bucket=self.bucket)

    async def download(self, filename: str) -> AsyncGenerator[bytes, None]:
        response = await asyncio.to_thread(
            self._client.get_object, Bucket=self.bucket, Key=filename
        )
        for chunk in response["Body"].iter_chunks(32 * 1024):
            yield chunk

    async def list_files(self) -> list[str]:
        response = await asyncio.to_thread(
            self._client.list_objects_v2, Bucket=self.bucket
        )
        return [obj["Key"] for obj in response.get("Contents", [])]


def create_storage_service() -> StorageService:
    """Factory — returns LocalStorageService or S3StorageService based on USE_S3_STORAGE."""
    if settings.USE_S3_STORAGE:
        logger.info("storage_service_init", backend="s3", bucket=settings.S3_BUCKET)
        return S3StorageService()
    logger.info(
        "storage_service_init",
        backend="local",
        path=settings.DOCUMENT_STORAGE_PATH,
    )
    return LocalStorageService()


storage_service: StorageService = create_storage_service()
