"""File-serving endpoint — proxy documents from StorageService (local PVC or S3).

Previously proxied from MinIO directly. Now uses the unified StorageService
so the backend doesn't need MinIO credentials at all.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.logging import logger
from app.services.storage_service import storage_service

router = APIRouter()


@router.get("/{filename:path}")
async def get_file_proxy(filename: str) -> StreamingResponse:
    """Stream a document from the configured storage backend."""
    logger.info("file_access_start", filename=filename)
    try:
        return StreamingResponse(
            storage_service.download(filename),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"inline; filename={filename}"},
        )
    except FileNotFoundError as exc:
        logger.warning("file_not_found", filename=filename)
        raise HTTPException(status_code=404, detail=f"File not found: {filename}") from exc
    except Exception as exc:
        logger.error("file_access_failed", filename=filename, error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc
