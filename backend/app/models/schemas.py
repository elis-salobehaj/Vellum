from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Citation(BaseModel):
    source: str
    page: int
    text: str
    score: Optional[float] = None

class ModelConfig(BaseModel):
    id: str
    name: str
    provider: str # openai, anthropic, azure, etc
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    deployment_name: Optional[str] = None # For Azure
    is_active: bool = False

class ChatRequest(BaseModel):
    message: str
    model_id: Optional[str] = None # If null, use default active
    # History passed from frontend (deprecated if using server-side session, but kept for compat)
    history: Optional[List[Dict[str, Any]]] = []
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    citations: List[Citation]
    metadata: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, Any]]] = None
    session_id: Optional[str] = None
