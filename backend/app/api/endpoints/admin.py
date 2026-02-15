from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List, AsyncGenerator
from app.models.schemas import ModelConfig, IngestRequest
from app.core.auth import get_current_user
from app.core.config import settings
from app.core.logging import logger
import os
import time
from minio import Minio

router = APIRouter()

# In-memory store for MVP. In production, use DB.
MODEL_CONFIGS: List[ModelConfig] = [
    ModelConfig(id="gemini-1.5-flash", name="Gemini 1.5 Flash", provider="google", is_active=False),
    ModelConfig(id="gpt-4", name="GPT-4", provider="openai", is_active=False),
    ModelConfig(id="claude-3-sonnet", name="Claude 3.5 Sonnet", provider="anthropic"),
    # Production Model via KServe
    ModelConfig(id="/mnt/models/Qwen2.5-1.5B-Instruct", name="Qwen 2.5 1.5B (KServe)", provider="kubeflow", is_active=True),
]

@router.get("/models", response_model=List[ModelConfig])
async def get_models(_: dict = Depends(get_current_user)):
    # TODO: Implement RBAC check here (e.g., if _.role != 'admin': raise 403)
    logger.debug("admin_get_models", count=len(MODEL_CONFIGS))
    return MODEL_CONFIGS

@router.post("/models", response_model=ModelConfig)
async def create_model(config: ModelConfig, _: dict = Depends(get_current_user)):
    # TODO: Implement RBAC check here (e.g., if _.role != 'admin': raise 403)
    logger.info("admin_create_model", model_id=config.id, provider=config.provider)
    # Check if id exists
    if any(m.id == config.id for m in MODEL_CONFIGS):
        logger.warning("admin_create_model_duplicate", model_id=config.id)
        raise HTTPException(status_code=400, detail="Model ID already exists")
    
    if config.is_active:
        logger.info("admin_model_activating", model_id=config.id)
        for m in MODEL_CONFIGS:
            m.is_active = False
            
    MODEL_CONFIGS.append(config)
    return config

@router.put("/models/{model_id}", response_model=ModelConfig)
async def update_model(model_id: str, config: ModelConfig, _: dict = Depends(get_current_user)):
    # TODO: RBAC check
    # Current Implementation:
    # This is a placeholder. In a production environment using OIDC (like Keycloak/Dex),
    # we would check 'current_user' for specific roles (e.g. 'admin') before allowing writes.
    # For now, any authenticated user can perform these actions.
    logger.info("admin_update_model", model_id=model_id, is_active=config.is_active)
    for i, m in enumerate(MODEL_CONFIGS):
        if m.id == model_id:
            if config.is_active:
                for existing in MODEL_CONFIGS:
                    existing.is_active = False
            MODEL_CONFIGS[i] = config
            return config
    logger.error("admin_update_model_not_found", model_id=model_id)
    raise HTTPException(status_code=404, detail="Model not found")


@router.post("/upload-and-ingest")
async def upload_and_ingest(current_user: dict = Depends(get_current_user)):
    """
    Trigger the full Upload & Ingest process.
    Streams logs back to the client.
    """
    async def log_generator() -> AsyncGenerator[str, None]:
        user_id = current_user.get("user", "unknown")
        logger.info("admin_ingest_process_start", user=user_id)
        yield "🚀 Starting Upload & Ingest Process...\n"
        
        # Configuration
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
        source_dir = os.path.join(base_dir, "data", "source_documents")
        
        # 1. Initialize Minio Client
        try:
            endpoint = settings.MINIO_ENDPOINT.replace("http://", "").replace("https://", "")
            client = Minio(
                endpoint,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=False
            )
            logger.debug("admin_minio_connected")
            yield "✅ Connected to Minio.\n"
        except Exception as e:
            logger.error("admin_minio_connect_failed", error=str(e))
            yield f"❌ Failed to connect to Minio: {e}\n"
            return

        # 2. Create Bucket if not exists
        try:
            if not client.bucket_exists(settings.MINIO_BUCKET):
                client.make_bucket(settings.MINIO_BUCKET)
                logger.info("admin_bucket_created", bucket=settings.MINIO_BUCKET)
                yield f"✅ Created bucket '{settings.MINIO_BUCKET}'.\n"
            else:
                yield f"ℹ️  Bucket '{settings.MINIO_BUCKET}' already exists.\n"
        except Exception as e:
            logger.error("admin_bucket_check_failed", bucket=settings.MINIO_BUCKET, error=str(e))
            yield f"❌ Failed to ensure bucket exists: {e}\n"
            return

        # 3. Upload Files
        if not os.path.exists(source_dir):
             logger.warning("admin_source_dir_missing", path=source_dir)
             yield f"⚠️ Source directory not found: {source_dir}\n"
        else:
            files = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]
            if not files:
                logger.warning("admin_no_files_found", path=source_dir)
                yield "⚠️  No files found in source directory.\n"
            
            for filename in files:
                file_path = os.path.join(source_dir, filename)
                try:
                    client.fput_object(settings.MINIO_BUCKET, filename, file_path)
                    logger.debug("admin_file_uploaded", filename=filename)
                    yield f"   ⬆️  Uploaded: {filename}\n"
                except Exception as e:
                    logger.error("admin_file_upload_failed", filename=filename, error=str(e))
                    yield f"   ❌ Failed to upload {filename}: {e}\n"

        # 4. Trigger Ingestion
        yield "🔄 Triggering Ingestion Pipeline...\n"
        from app.services.kfp_service import kfp_service
        
        try:
            logger.info("admin_triggering_kfp")
            result = await kfp_service.trigger_ingestion(
                bucket=settings.MINIO_BUCKET,
                cleanup=True
            )
            
            if result.get("status") == "success":
                logger.info("admin_kfp_trigger_success", run_id=result.get("run_id"))
                yield f"✅ Ingestion Triggered Successfully: {result['message']}\n"
                yield f"Run ID: {result.get('run_id')}\n"
            elif result.get("status") == "redirect":
                 logger.warning("admin_kfp_trigger_redirect", message=result['message'])
                 yield f"⚠️  {result['message']}\n"
                 yield f"Details: {result.get('details')}\n"
            else:
                logger.error("admin_kfp_trigger_failed", result=result)
                yield f"❌ Ingestion Failed: {result}\n"
                
        except Exception as e:
             logger.error("admin_kfp_trigger_exception", error=str(e))
             yield f"❌ Failed to trigger ingestion: {e}\n"
             
        logger.info("admin_ingest_process_complete")
        yield "🏁 Process Complete.\n"

    return StreamingResponse(log_generator(), media_type="text/plain")
