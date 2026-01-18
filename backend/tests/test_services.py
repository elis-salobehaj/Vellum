
import sys
import pytest
from unittest.mock import MagicMock, patch
from importlib import reload

# Helper to remove mocks if they exist from other tests
def clean_sys_modules():
    modules_to_clean = [
        "app.services.history_service",
        "app.services.llm_service",
        "app.services.rag_service"
    ]
    for m in modules_to_clean:
        if m in sys.modules and isinstance(sys.modules[m], MagicMock):
            del sys.modules[m]

# --- Auth Tests ---
@pytest.mark.asyncio
async def test_auth_validate_token_success():
    from app.core import auth
    # Reload auth to ensure config overrides if needed, generally logic is straightforward
    
    with patch("app.core.config.settings.BYPASS_AUTH", False):
        user = await auth.get_current_user("valid-token")
        assert user["user"] == "test-user"

@pytest.mark.asyncio
async def test_auth_validate_token_missing():
    from app.core import auth
    from fastapi import HTTPException
    
    with patch("app.core.config.settings.BYPASS_AUTH", False):
        with pytest.raises(HTTPException):
            await auth.get_current_user(None)

# --- History Service Tests ---
def test_history_service_logic():
    clean_sys_modules()
    # Import inside function to avoid early binding if we just deleted it
    from app.services import history_service as hs_module
    reload(hs_module) # Reload to be sure we get the real class
    
    service = hs_module.HistoryService()
    
    # Patch the global CONVERSATIONS in the module to isolate test
    with patch.object(hs_module, "CONVERSATIONS", {}) as mock_db:
        service.add_message("sess1", "user", "Hello")
        
        # Check Messages
        msgs = service.get_messages("sess1")
        assert len(msgs) == 1
        assert msgs[0]["content"] == "Hello"
        assert msgs[0]["role"] == "user"
        
        # Check Recent
        recent = service.get_recent_conversations("uid")
        assert len(recent) == 1
        assert recent[0]["id"] == "sess1"
        assert "Hello" in recent[0]["title"]

# --- LLM Service Tests ---
@pytest.mark.asyncio
async def test_llm_service_providers():
    clean_sys_modules()
    
    # Mock Google and OpenAILike imports
    sys.modules["llama_index.llms.gemini"] = MagicMock()
    sys.modules["llama_index.llms.openai_like"] = MagicMock()
    
    from app.services import llm_service as ls_module
    from app.models.schemas import ModelConfig
    reload(ls_module)
    
    service = ls_module.LLMService()
    
    # 1. Test OpenAI
    config_openai = ModelConfig(id="gpt-4", name="GPT4", provider="openai", api_key="sk-test")
    llm = await service._get_llm(config_openai)
    assert llm.model == "gpt-4"
    
    # 2. Test Kubeflow
    config_kfp = ModelConfig(id="qwen", name="Qwen", provider="kubeflow", base_url="http://kfp:80")
    llm = await service._get_llm(config_kfp)
    # OpenAILike mock check
    
    # 3. Test Google
    with patch.dict("os.environ", {"GOOGLE_API_KEY": "fake-key"}):
        config_google = ModelConfig(id="gemini-1.5", name="Gemini", provider="google")
        await service._get_llm(config_google)
        # Should succeed with mock
        
    # 4. Invalid
    with pytest.raises(ValueError):
        await service._get_llm(ModelConfig(id="bad", name="bad", provider="unknown"))
