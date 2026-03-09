from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any


class Citation(BaseModel):
    source: str
    page: int
    text: str
    score: Optional[float] = None


class ModelConfig(BaseModel):
    id: str
    model_api_path: str
    name: str
    provider: str  # openai, anthropic, azure, etc
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    deployment_name: Optional[str] = None  # For Azure
    is_active: bool = False

    @field_validator("model_api_path")
    @classmethod
    def validate_model_api_path(cls, value: str) -> str:
        cleaned = value.strip().strip("/")
        if not cleaned:
            raise ValueError("model_api_path must not be empty")
        return cleaned


class ChatRequest(BaseModel):
    message: str
    model_id: Optional[str] = None  # If null, use default active
    # History passed from frontend (deprecated if using server-side session, but kept for compat)
    history: Optional[List[Dict[str, Any]]] = []
    session_id: Optional[str] = None
    context_window: int = 5
    use_graph: bool = False


class ChatResponse(BaseModel):
    response: str
    citations: List[Citation]
    metadata: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, Any]]] = None
    session_id: Optional[str] = None


class IngestRequest(BaseModel):
    bucket: Optional[str] = None
    prefix: Optional[str] = ""
    cleanup: bool = False
