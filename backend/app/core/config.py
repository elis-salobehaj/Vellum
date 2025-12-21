from pydantic_settings import BaseSettings

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
    CHROMA_PERSIST_DIRECTORY: str = "data/chroma"
    
    # Security
    BYPASS_AUTH: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()
