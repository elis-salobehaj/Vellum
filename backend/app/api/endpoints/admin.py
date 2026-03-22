from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List, AsyncGenerator
from app.models.schemas import ModelConfig
from app.core.auth import get_current_user
from app.core.config import settings
from app.core.logging import logger
import os
import tempfile

router = APIRouter()


def _default_active_model_id() -> str:
    if settings.AWS_BEDROCK_API_KEY.strip():
        return "global.anthropic.claude-sonnet-4-6"
    if settings.OPENAI_API_KEY.strip():
        return "gpt-4o"
    if settings.GOOGLE_API_KEY.strip():
        return "gemini-1.5-flash"
    return "Qwen3.5-2B"


# In-memory store for MVP. In production, use DB.
MODEL_CONFIGS: List[ModelConfig] = [
    ModelConfig(
        id="gemini-1.5-flash",
        model_api_path="gemini-1-5-flash",
        name="Gemini 1.5 Flash",
        provider="google",
        is_active=_default_active_model_id() == "gemini-1.5-flash",
    ),
    ModelConfig(
        id="gpt-4o",
        model_api_path="gpt-4o",
        name="GPT-4o",
        provider="openai",
        is_active=_default_active_model_id() == "gpt-4o",
    ),
    ModelConfig(
        id="global.anthropic.claude-sonnet-4-6",
        model_api_path="claude-sonnet-4-6",
        name="Claude Sonnet 4.6",
        provider="aws_bedrock",
        is_active=_default_active_model_id() == "global.anthropic.claude-sonnet-4-6",
    ),
    ModelConfig(
        id="Qwen3.5-2B",
        model_api_path="qwen-3-5-2b",
        name="Qwen 3.5 2B",
        provider="ray",
        is_active=_default_active_model_id() == "Qwen3.5-2B",
    ),
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
    if any(m.model_api_path == config.model_api_path for m in MODEL_CONFIGS):
        logger.warning(
            "admin_create_model_duplicate_api_path",
            model_api_path=config.model_api_path,
        )
        raise HTTPException(status_code=400, detail="Model API path already exists")

    if config.is_active:
        logger.info("admin_model_activating", model_id=config.id)
        for m in MODEL_CONFIGS:
            m.is_active = False

    MODEL_CONFIGS.append(config)
    return config


@router.put("/models/{model_api_path}", response_model=ModelConfig)
async def update_model(
    model_api_path: str, config: ModelConfig, _: dict = Depends(get_current_user)
):
    # TODO: RBAC check
    # Current Implementation:
    # This is a placeholder. In a production environment using OIDC (like Keycloak/Dex),
    # we would check 'current_user' for specific roles (e.g. 'admin') before allowing writes.
    # For now, any authenticated user can perform these actions.
    logger.info(
        "admin_update_model",
        model_api_path=model_api_path,
        model_id=config.id,
        is_active=config.is_active,
    )
    if config.model_api_path != model_api_path:
        logger.error(
            "admin_update_model_api_path_mismatch",
            path_model_api_path=model_api_path,
            body_model_api_path=config.model_api_path,
        )
        raise HTTPException(status_code=400, detail="Model API path mismatch")

    for i, m in enumerate(MODEL_CONFIGS):
        if m.model_api_path == model_api_path:
            if config.is_active:
                for existing in MODEL_CONFIGS:
                    existing.is_active = False
            MODEL_CONFIGS[i] = config
            return config
    logger.error("admin_update_model_not_found", model_api_path=model_api_path)
    raise HTTPException(status_code=404, detail="Model not found")


@router.post("/upload-and-ingest")
async def upload_and_ingest(
    batch_size: int = 25,
    reset_progress: bool = False,
    cleanup: bool = False,
    current_user: dict = Depends(get_current_user),
):
    """
    Trigger the full Upload & Ingest process.
    Streams logs back to the client.
    """

    async def log_generator() -> AsyncGenerator[str, None]:
        user_id = current_user.get("user", "unknown")
        logger.info("admin_ingest_process_start", user=user_id)
        yield "🚀 Starting Upload & Ingest Process...\n"

        storage_path = settings.DOCUMENT_STORAGE_PATH
        yield f"ℹ️  Document storage backend: {'S3' if settings.USE_S3_STORAGE else 'local'} ({storage_path})\n"

        if cleanup:
            logger.info("admin_ingest_clean_slate_requested", user=user_id)
            yield "🧹 Clean-slate ingestion requested; existing collection contents will be replaced.\n"

        # Trigger Ingestion
        if settings.INGESTION_MODE == "direct":
            yield "🔄 Running Direct Ingestion...\n"
            from app.services.direct_ingestion_service import direct_ingestion_service

            try:
                direct_logs = await direct_ingestion_service.run(
                    cleanup=cleanup,
                    batch_size=batch_size,
                    reset_progress=reset_progress,
                )
                for line in direct_logs:
                    yield f"{line}\n"
                status = await direct_ingestion_service.get_status()
                yield (
                    "📈 Status: "
                    f"{status['indexed_source_doc_count']}/{status['total_doc_count']} indexed, "
                    f"status={status['status']}\n"
                )
                if status.get("recent_skipped_files"):
                    yield (
                        "⚠️ Recent skipped files: "
                        + ", ".join(status["recent_skipped_files"])
                        + "\n"
                    )
            except Exception as e:
                logger.error("admin_direct_ingest_exception", error=str(e))
                yield f"❌ Direct ingestion failed: {e}\n"
        else:
            yield "🔄 Triggering Dagster Ingestion Job...\n"
            from app.services.dagster_service import dagster_service

            try:
                result = await dagster_service.trigger_ingestion()
                if result.get("status") == "success":
                    logger.info("admin_dagster_trigger_success", run_id=result.get("run_id"))
                    yield f"✅ Ingestion Triggered: {result['message']}\n"
                    yield f"Run ID: {result.get('run_id')}\n"
                else:
                    logger.error("admin_dagster_trigger_failed", result=result)
                    yield f"❌ Ingestion Failed: {result.get('message')}\n"
            except Exception as e:
                logger.error("admin_dagster_trigger_exception", error=str(e))
                yield f"❌ Failed to trigger Dagster ingestion: {e}\n"

        logger.info("admin_ingest_process_complete")
        yield "🏁 Process Complete.\n"

    return StreamingResponse(log_generator(), media_type="text/plain")


@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a document to the configured storage backend (local PVC or S3).
    """
    from app.services.storage_service import storage_service

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    user_id = current_user.get("user", "unknown")
    logger.info("admin_file_upload_start", filename=file.filename, user=user_id)

    try:
        # Write upload to a temp file then hand off to storage service
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        await storage_service.upload(file.filename, tmp_path)
        os.unlink(tmp_path)
        logger.info("admin_file_upload_success", filename=file.filename)
        return {"status": "ok", "filename": file.filename}
    except Exception as e:
        logger.error("admin_file_upload_failed", filename=file.filename, error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/ingestion-status")
async def ingestion_status(current_user: dict = Depends(get_current_user)):
    del current_user

    from app.services.direct_ingestion_service import direct_ingestion_service

    try:
        return await direct_ingestion_service.get_status()
    except Exception as exc:
        logger.error("admin_ingestion_status_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc
