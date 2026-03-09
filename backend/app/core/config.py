from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Info
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Vellum"

    # Provider Selection (Priority: Bedrock > OpenAI > Google > Local)
    use_bedrock: bool = False
    use_openai: bool = False
    use_google: bool = False
    use_local_model: bool = False

    # Entra ID / Azure AD
    AZURE_CLIENT_ID: str = ""
    AZURE_TENANT_ID: str = ""
    AZURE_CLIENT_SECRET: str = ""
    AZURE_AUTHORITY: str = "https://login.microsoftonline.com/common"

    # Google
    GOOGLE_API_KEY: str = ""

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = "https://api.openai.com/v1"

    # Kubeflow / KServe
    LLM_SERVICE_URL: str = (
        "http://llm-service-predictor.kubeflow-vellum.svc.cluster.local:80/v1"
    )
    KFP_HOST: str = "http://ml-pipeline.kubeflow.svc.cluster.local:8888"
    KFP_NAMESPACE: str = "kubeflow-vellum"
    KFP_USER_ID: str = "vellum@example.com"
    INGESTION_MODE: str = "kfp"

    # AWS Bedrock
    AWS_BEDROCK_API_KEY: str = ""
    AWS_REGION: str = "us-east-1"

    # Vector DB
    QDRANT_HOST: str = "qdrant.qdrant.svc.cluster.local"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "vellum"

    # MinIO
    MINIO_ENDPOINT: str = "minio-service.kubeflow.svc:9000"
    MINIO_ACCESS_KEY: str = "minio"
    MINIO_SECRET_KEY: str = "minio123"
    MINIO_BUCKET: str = "documents"

    # Embeddings
    EMBEDDING_MODEL_NAME: str = "text-embedding-3-small"
    EMBEDDINGS_SERVICE_URL: str = (
        "http://embeddings-service.kubeflow-vellum.svc.cluster.local/v1"
    )

    # Security
    BYPASS_AUTH: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def model_post_init(self, __context) -> None:
        """
        Sync critical settings to os.environ for libraries that rely on them.
        """
        import os

        if self.AWS_REGION:
            os.environ["AWS_REGION"] = self.AWS_REGION
            os.environ["AWS_DEFAULT_REGION"] = self.AWS_REGION

        # Disable IMDS for local development to prevent long credential timeouts.
        os.environ["AWS_EC2_METADATA_DISABLED"] = "true"

    @property
    def active_provider(self) -> str:
        """Returns active provider based on priority."""
        if self.use_bedrock:
            return "aws_bedrock"
        if self.use_openai:
            return "openai"
        if self.use_google:
            return "google"
        if self.use_local_model:
            return "kubeflow"  # or local
        return "openai"  # Default fallback


settings = Settings()
