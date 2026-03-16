from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List, AsyncGenerator
from app.models.schemas import ModelConfig
from app.core.auth import get_current_user
from app.core.config import settings
from app.core.logging import logger
import os
from minio import Minio

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
        provider="kubeflow",
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

        # Configuration
        base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../../")
        )
        source_dir_candidates = [
            os.path.join(base_dir, "data", "source_documents"),
            "/data/source_documents",
        ]
        source_dir = next(
            (path for path in source_dir_candidates if os.path.exists(path)),
            source_dir_candidates[0],
        )

        if cleanup:
            logger.info("admin_ingest_clean_slate_requested", user=user_id)
            yield "🧹 Clean-slate ingestion requested; existing collection contents will be replaced.\n"

        yield f"ℹ️  Using source directory: {source_dir}\n"

        # 1. Initialize Minio Client
        try:
            endpoint = settings.MINIO_ENDPOINT.replace("http://", "").replace(
                "https://", ""
            )
            client = Minio(
                endpoint,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=False,
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
            logger.error(
                "admin_bucket_check_failed", bucket=settings.MINIO_BUCKET, error=str(e)
            )
            yield f"❌ Failed to ensure bucket exists: {e}\n"
            return

        # 3. Upload Files
        if not os.path.exists(source_dir):
            logger.warning("admin_source_dir_missing", path=source_dir)
            yield f"⚠️ Source directory not found: {source_dir}\n"
        else:
            files = [
                f
                for f in os.listdir(source_dir)
                if os.path.isfile(os.path.join(source_dir, f))
            ]
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
                    logger.error(
                        "admin_file_upload_failed", filename=filename, error=str(e)
                    )
                    yield f"   ❌ Failed to upload {filename}: {e}\n"

        # 4. Trigger Ingestion
        if settings.INGESTION_MODE == "direct":
            yield "🔄 Running Direct Ingestion...\n"
            from app.services.direct_ingestion_service import direct_ingestion_service

            try:
                direct_logs = direct_ingestion_service.run(
                    bucket=settings.MINIO_BUCKET,
                    cleanup=cleanup,
                    batch_size=batch_size,
                    reset_progress=reset_progress,
                )
                for line in direct_logs:
                    yield f"{line}\n"
                status = direct_ingestion_service.get_status(
                    bucket=settings.MINIO_BUCKET
                )
                yield (
                    "📈 Status: "
                    f"{status['indexed_source_doc_count']}/{status['bucket_object_count']} indexed, "
                    f"pending {status['pending_source_object_count']}, status={status['status']}\n"
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
            yield "🔄 Triggering Ingestion Pipeline...\n"
            from app.services.kfp_service import kfp_service

            try:
                logger.info("admin_triggering_kfp")
                kfp_user_id = None if settings.BYPASS_AUTH else current_user.get("user")
                result = await kfp_service.trigger_ingestion(
                    bucket=settings.MINIO_BUCKET,
                    cleanup=cleanup,
                    user_id=kfp_user_id,
                )

                if result.get("status") == "success":
                    logger.info(
                        "admin_kfp_trigger_success", run_id=result.get("run_id")
                    )
                    yield f"✅ Ingestion Triggered Successfully: {result['message']}\n"
                    yield f"Run ID: {result.get('run_id')}\n"
                elif result.get("status") == "redirect":
                    logger.warning(
                        "admin_kfp_trigger_redirect", message=result["message"]
                    )
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


@router.get("/ingestion-status")
async def ingestion_status(current_user: dict = Depends(get_current_user)):
    del current_user

    from app.services.direct_ingestion_service import direct_ingestion_service

    try:
        return direct_ingestion_service.get_status(bucket=settings.MINIO_BUCKET)
    except Exception as exc:
        logger.error("admin_ingestion_status_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc
