from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Vellum"
    
    # Entra ID / Azure AD
    AZURE_CLIENT_ID: str = ""
    AZURE_TENANT_ID: str = ""
    AZURE_CLIENT_SECRET: str = ""
    AZURE_AUTHORITY: str = "https://login.microsoftonline.com/common"
    
    # Google
    GOOGLE_API_KEY: str = ""
    
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
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    EMBEDDINGS_SERVICE_URL: str = "http://embeddings-service.kubeflow-user-example-com/v1"
    
    # Security
    BYPASS_AUTH: bool = True
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
