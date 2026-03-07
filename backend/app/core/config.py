from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import Any


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
    OPENAI_KEY: str = ""  # Legacy/User provided
    OPENAI_API_BASE: str = "https://api.openai.com/v1"

    # Kubeflow / KServe
    LLM_SERVICE_URL: str = (
        "http://llm-service-predictor.kubeflow-vellum.svc.cluster.local:80/v1"
    )
    KFP_HOST: str = "http://ml-pipeline.kubeflow.svc.cluster.local:8888"

    # AWS Bedrock
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    AWS_BEARER_TOKEN_BEDROCK: str = ""  # Custom format
    AWS_BEDROCK_API_KEY: str = "" # Alias for Bearer Token if used key-style


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

    @model_validator(mode="before")
    @classmethod
    def parse_env_vars(cls, data: Any) -> Any:
        # 1. Map OPENAI_KEY -> OPENAI_API_KEY
        if "OPENAI_KEY" in data and not data.get("OPENAI_API_KEY"):
            data["OPENAI_API_KEY"] = data["OPENAI_KEY"]

        # 2. Parse AWS Bearer Token if standard credentials are missing
        # Format: ABSK<Base64(ID:Secret)>
        # 2. Parse AWS Bearer Token or API Key
        # Format: ABSK<Base64(ID:Secret)>
        bedrock_token = data.get("AWS_BEARER_TOKEN_BEDROCK") or data.get("AWS_BEDROCK_API_KEY")
        if bedrock_token and not data.get("AWS_ACCESS_KEY_ID"):
            try:
                import base64
                # Remove prefix if present (assuming ABSK is a prefix based on user input,
                # but if it's just base64, we try to decode the whole thing or after a prefix)
                # The user showed: ABSKQmVk...
                # "ABSK" might be "AWS Bedrock Shared Key" marker?
                # Let's try to decode the payload after 'ABSK'

                payload = bedrock_token
                if payload.startswith("ABSK"):
                    payload = payload[4:]

                decoded = base64.b64decode(payload).decode("utf-8")
                if ":" in decoded:
                    key_id, secret = decoded.split(":", 1)
                    data["AWS_ACCESS_KEY_ID"] = key_id
                    data["AWS_SECRET_ACCESS_KEY"] = secret.strip()
            except Exception:
                pass  # Fallback to standard flow or fail later

        return data

    def model_post_init(self, __context) -> None:
        """
        Sync critical settings to os.environ for libraries that rely on them (boto3).
        """
        import os

        # AWS variables (boto3 checks os.environ)
        if self.AWS_REGION:
            os.environ["AWS_REGION"] = self.AWS_REGION
            os.environ["AWS_DEFAULT_REGION"] = self.AWS_REGION
        
        if self.AWS_ACCESS_KEY_ID:
            os.environ["AWS_ACCESS_KEY_ID"] = self.AWS_ACCESS_KEY_ID
        
        if self.AWS_SECRET_ACCESS_KEY:
            os.environ["AWS_SECRET_ACCESS_KEY"] = self.AWS_SECRET_ACCESS_KEY

        # Critical: Disable IMDS for local development to prevent long timeouts
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
            return "kubeflow" # or local
        return "openai"  # Default fallback


settings = Settings()
