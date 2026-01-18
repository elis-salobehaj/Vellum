import kfp
from app.core.config import settings
import os

class KFPService:
    def __init__(self):
        # In-cluster address for ml-pipeline
        self.host = os.getenv("KFP_HOST", "http://ml-pipeline.kubeflow.svc.cluster.local:8888")
        self.client = None

    def get_client(self):
        if not self.client:
            try:
                self.client = kfp.Client(host=self.host)
                # Inject auth header for multi-user Kubeflow
                for key, value in self.client.__dict__.items():
                    if hasattr(value, 'api_client'):
                        value.api_client.default_headers['kubeflow-userid'] = 'user@example.com'
            except Exception as e:
                print(f"ERROR: Could not connect to KFP at {self.host}: {e}")
        return self.client

    async def trigger_ingestion(self, bucket: str = None, prefix: str = "", cleanup: bool = False):
        client = self.get_client()
        if not client:
            return {"status": "error", "message": "KFP connection failed"}

        bucket = bucket or settings.MINIO_BUCKET
        
        # Parameters for the pipeline
        params = {
            "bucket": bucket,
            "prefix": prefix,
            "minio_endpoint": settings.MINIO_ENDPOINT,
            "qdrant_host": "qdrant.qdrant.svc.cluster.local",
            "qdrant_port": 6333,
            "chunk_size": 512,
            "chunk_overlap": 40,
            "splitter_mode": "fixed",
            "max_docs": 1000,
            "model_name": "BAAI/bge-small-en-v1.5",
            "embeddings_service_url": settings.EMBEDDINGS_SERVICE_URL,
            "cleanup": cleanup
        }

        try:
            # We use create_run_from_pipeline_func to launch immediately
            from kubeflow.pipelines.ingestion.pipeline import ingestion_pipeline
            
            # Recompile to YAML so we can use it with the client
            from kfp import compiler
            yaml_path = "/tmp/ingestion_pipeline.yaml"
            compiler.Compiler().compile(pipeline_func=ingestion_pipeline, package_path=yaml_path)

            # Some KFP versions allow passing the header via environment or session
            # If the SDK call fails, we return a manual URL
            run_result = client.create_run_from_pipeline_package(
                pipeline_file=yaml_path,
                arguments=params,
                experiment_name="Vellum_Ingestion"
            )
            
            return {
                "status": "success", 
                "run_id": run_result.run_id,
                "message": f"Ingestion triggered. Run ID: {run_result.run_id}"
            }
        except Exception as e:
            # Fallback message with UI link
            return {
                "status": "redirect",
                "message": "KFP Auth required. Please trigger the pipeline manually at: http://localhost:8080/_/pipeline/#/pipelines",
                "details": str(e)
            }

kfp_service = KFPService()
