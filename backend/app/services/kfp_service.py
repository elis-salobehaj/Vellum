import kfp
from app.core.config import settings
from app.core.logging import logger


class KFPService:
    def __init__(self):
        # In-cluster address for ml-pipeline
        self.host = settings.KFP_HOST

    def get_client(self, user_id: str):
        """Build a KFP client with the correct multi-user identity headers."""

        try:
            logger.debug(
                "kfp_client_init",
                host=self.host,
                namespace=settings.KFP_NAMESPACE,
                user_id=user_id,
            )
            client = kfp.Client(host=self.host, namespace=settings.KFP_NAMESPACE)
            # Inject auth headers for multi-user Kubeflow environments
            self._inject_auth_headers(client, user_id)
            return client
        except Exception as e:
            logger.error("kfp_connection_failed", host=self.host, error=str(e))
            return None

    def _inject_auth_headers(self, client, user_id: str):
        """Helper to inject necessary identity headers into KFP internal API clients."""
        for attr_name, attr_value in client.__dict__.items():
            if hasattr(attr_value, "api_client"):
                logger.debug("kfp_injecting_headers", client_attr=attr_name)
                # Both headers are used by various Kubeflow ingress/auth configurations
                attr_value.api_client.default_headers["kubeflow-userid"] = (
                    user_id
                )
                attr_value.api_client.default_headers[
                    "X-Goog-Authenticated-User-Email"
                ] = user_id

    async def trigger_ingestion(
        self,
        bucket: str = None,
        prefix: str = "",
        cleanup: bool = False,
        user_id: str | None = None,
    ):
        effective_user_id = user_id or settings.KFP_USER_ID
        client = self.get_client(effective_user_id)
        if not client:
            return {"status": "error", "message": "KFP connection failed"}

        bucket = bucket or settings.MINIO_BUCKET
        logger.info(
            "kfp_trigger_ingestion", bucket=bucket, prefix=prefix, cleanup=cleanup
        )

        # Determine internal endpoints for pipeline (which runs inside cluster)
        # If running locally (hybrid), settings point to localhost, but pipeline needs cluster DNS.
        pipeline_minio = settings.MINIO_ENDPOINT
        if "localhost" in pipeline_minio or "127.0.0.1" in pipeline_minio:
            pipeline_minio = "minio-service.kubeflow.svc.cluster.local:9000"

        pipeline_embeddings = settings.EMBEDDINGS_SERVICE_URL
        if "localhost" in pipeline_embeddings or "127.0.0.1" in pipeline_embeddings:
            pipeline_embeddings = (
                "http://embeddings-service.kubeflow-vellum.svc.cluster.local/v1"
            )

        # Parameters for the pipeline
        params = {
            "bucket": bucket,
            "prefix": prefix,
            "minio_endpoint": pipeline_minio,
            "qdrant_host": "qdrant.qdrant.svc.cluster.local",
            "qdrant_port": 6333,
            "chunk_size": 512,
            "chunk_overlap": 40,
            "splitter_mode": "fixed",
            "max_docs": 1000,
            "model_name": "BAAI/bge-small-en-v1.5",
            "embeddings_service_url": pipeline_embeddings,
            "cleanup": cleanup,
        }

        try:
            # We use create_run_from_pipeline_func to launch immediately
            from vellum_ingestion.pipeline import ingestion_pipeline

            # Recompile to YAML so we can use it with the client
            from kfp import compiler

            yaml_path = "/tmp/ingestion_pipeline.yaml"
            logger.debug("kfp_compiling_pipeline", path=yaml_path)
            compiler.Compiler().compile(
                pipeline_func=ingestion_pipeline, package_path=yaml_path
            )

            logger.info(
                "kfp_creating_run",
                experiment="Vellum_Ingestion",
                namespace=settings.KFP_NAMESPACE,
                user_id=effective_user_id,
            )
            run_result = client.create_run_from_pipeline_package(
                pipeline_file=yaml_path,
                arguments=params,
                experiment_name="Vellum_Ingestion",
                namespace=settings.KFP_NAMESPACE,
            )

            logger.info("kfp_trigger_success", run_id=run_result.run_id)
            return {
                "status": "success",
                "run_id": run_result.run_id,
                "message": f"Ingestion triggered. Run ID: {run_result.run_id}",
            }
        except Exception as e:
            logger.warning("kfp_trigger_auth_required", error=str(e))
            # Fallback message with UI link
            return {
                "status": "redirect",
                "message": "KFP Auth required. Please trigger the pipeline manually at: http://localhost:8080/_/pipeline/#/pipelines",
                "details": str(e),
            }


kfp_service = KFPService()
