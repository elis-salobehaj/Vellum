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

    # Ray Serve (local LLM)
    LLM_SERVICE_URL: str = (
        "http://llm-service-head-svc.vellum-ray.svc.cluster.local:8000/v1"
    )

    # Dagster (replaces KFP)
    DAGSTER_GRAPHQL_URL: str = (
        "http://dagster-dagster-webserver.dagster.svc.cluster.local:3000/graphql"
    )
    INGESTION_MODE: str = "direct"  # "direct" | "dagster"

    # AWS Bedrock
    AWS_BEDROCK_API_KEY: str = ""
    AWS_REGION: str = "us-east-1"

    # Vector DB
    QDRANT_HOST: str = "qdrant.qdrant.svc.cluster.local"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "vellum"

    # Document Storage (replaces MinIO)
    USE_S3_STORAGE: bool = False
    DOCUMENT_STORAGE_PATH: str = "/data/documents"  # PVC mount path (local default)
    S3_BUCKET: str = "vellum-documents"
    S3_ENDPOINT: str = ""   # e.g. https://s3.us-east-1.amazonaws.com
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""

    # Embeddings
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
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
            return "ray"
        return "openai"  # Default fallback


settings = Settings()
