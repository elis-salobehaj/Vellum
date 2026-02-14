from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List, AsyncGenerator
from app.models.schemas import ModelConfig, IngestRequest
from app.core.auth import get_current_user
from app.core.config import settings
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
    return MODEL_CONFIGS

@router.post("/models", response_model=ModelConfig)
async def create_model(config: ModelConfig, _: dict = Depends(get_current_user)):
    # TODO: RBAC check
    # Check if id exists
    if any(m.id == config.id for m in MODEL_CONFIGS):
        raise HTTPException(status_code=400, detail="Model ID already exists")
    
    if config.is_active:
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
    for i, m in enumerate(MODEL_CONFIGS):
        if m.id == model_id:
            if config.is_active:
                for existing in MODEL_CONFIGS:
                    existing.is_active = False
            MODEL_CONFIGS[i] = config
            return config
    raise HTTPException(status_code=404, detail="Model not found")


@router.post("/upload-and-ingest")
async def upload_and_ingest(current_user: dict = Depends(get_current_user)):
    """
    Trigger the full Upload & Ingest process.
    Streams logs back to the client.
    """
    async def log_generator() -> AsyncGenerator[str, None]:
        yield "🚀 Starting Upload & Ingest Process...\n"
        
        # Configuration
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
        source_dir = os.path.join(base_dir, "data", "source_documents")
        
        # 1. Initialize Minio Client
        try:
            # Parse endpoint to remove protocol if present
            endpoint = settings.MINIO_ENDPOINT.replace("http://", "").replace("https://", "")
            
            client = Minio(
                endpoint,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=False
            )
            yield "✅ Connected to Minio.\n"
        except Exception as e:
            yield f"❌ Failed to connect to Minio: {e}\n"
            return

        # 2. Create Bucket if not exists
        try:
            if not client.bucket_exists(settings.MINIO_BUCKET):
                client.make_bucket(settings.MINIO_BUCKET)
                yield f"✅ Created bucket '{settings.MINIO_BUCKET}'.\n"
            else:
                yield f"ℹ️  Bucket '{settings.MINIO_BUCKET}' already exists.\n"
        except Exception as e:
            yield f"❌ Failed to ensure bucket exists: {e}\n"
            return

        # 3. Upload Files
        if not os.path.exists(source_dir):
             yield f"⚠️ Source directory not found: {source_dir}\n"
        else:
            files = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]
            if not files:
                yield "⚠️  No files found in source directory.\n"
            
            for filename in files:
                file_path = os.path.join(source_dir, filename)
                try:
                    client.fput_object(settings.MINIO_BUCKET, filename, file_path)
                    yield f"   ⬆️  Uploaded: {filename}\n"
                except Exception as e:
                    yield f"   ❌ Failed to upload {filename}: {e}\n"

        # 4. Trigger Ingestion
        yield "🔄 Triggering Ingestion Pipeline...\n"
        from app.services.kfp_service import kfp_service
        
        try:
            result = await kfp_service.trigger_ingestion(
                bucket=settings.MINIO_BUCKET,
                cleanup=True
            )
            
            if result.get("status") == "success":
                yield f"✅ Ingestion Triggered Successfully: {result['message']}\n"
                yield f"Run ID: {result.get('run_id')}\n"
            elif result.get("status") == "redirect":
                 yield f"⚠️  {result['message']}\n"
                 yield f"Details: {result.get('details')}\n"
            else:
                yield f"❌ Ingestion Failed: {result}\n"
                
        except Exception as e:
             yield f"❌ Failed to trigger ingestion: {e}\n"
             
        yield "🏁 Process Complete.\n"

    return StreamingResponse(log_generator(), media_type="text/plain")
