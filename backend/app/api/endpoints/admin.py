from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.schemas import ModelConfig
from app.core.auth import get_current_user

router = APIRouter()

# In-memory store for MVP. In production, use DB.
MODEL_CONFIGS: List[ModelConfig] = [
    ModelConfig(id="gemini-1.5-flash", name="Gemini 1.5 Flash", provider="google", is_active=False),
    ModelConfig(id="gpt-4", name="GPT-4", provider="openai", is_active=False),
    ModelConfig(id="claude-3-sonnet", name="Claude 3.5 Sonnet", provider="anthropic"),
    ModelConfig(id="llama3", name="Llama 3 (Ollama)", provider="ollama", is_active=False),
    ModelConfig(id="mistral", name="Mistral 7B (Ollama)", provider="ollama", is_active=True),
    ModelConfig(id="gemma2", name="Gemma 2 9B (Ollama)", provider="ollama", is_active=False),
    ModelConfig(id="gemma3:4b", name="Gemma 3 4B (Ollama)", provider="ollama", is_active=False),
    ModelConfig(id="llama3.2", name="Llama 3.2 3B (Ollama)", provider="ollama", is_active=False),
    ModelConfig(id="gemma:2b", name="Gemma 2B (Ollama)", provider="ollama", is_active=False),
]

@router.get("/models", response_model=List[ModelConfig])
async def get_models(_: dict = Depends(get_current_user)):
    # TODO: Implement RBAC check here (e.g., if _.role != 'admin': raise 403)
    return MODEL_CONFIGS

@router.post("/models", response_model=ModelConfig)
async def create_model(config: ModelConfig, _: dict = Depends(get_current_user)):
    # TODO: RBAC check
    # Check if id exists
    if any(m.id == config.id for m in MODEL_CONFIGS):
        raise HTTPException(status_code=400, detail="Model ID already exists")
    
    if config.is_active:
        for m in MODEL_CONFIGS:
            m.is_active = False
            
    MODEL_CONFIGS.append(config)
    return config

@router.put("/models/{model_id}", response_model=ModelConfig)
async def update_model(model_id: str, config: ModelConfig, _: dict = Depends(get_current_user)):
    # TODO: RBAC check
    for i, m in enumerate(MODEL_CONFIGS):
        if m.id == model_id:
            if config.is_active:
                for existing in MODEL_CONFIGS:
                    existing.is_active = False
            MODEL_CONFIGS[i] = config
            return config
    raise HTTPException(status_code=404, detail="Model not found")
