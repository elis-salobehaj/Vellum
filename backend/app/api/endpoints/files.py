from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from minio import Minio
from app.core.config import settings

router = APIRouter()

@router.get("/{filename:path}")
async def get_file_proxy(filename: str):
    """
    Proxy request to MinIO to serve the file directly.
    """
    try:
        # Initialize MinIO client locally for the proxy
        # We use the internal kubeflow svc endpoint
        client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )
        
        # Get object from MinIO
        response = client.get_object(settings.MINIO_BUCKET, filename)
        
        # Stream the response back to the user
        return StreamingResponse(
            response.stream(32*1024),
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
