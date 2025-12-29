
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
def test_llm_service_config():
    clean_sys_modules()
    from app.services import llm_service as ls_module
    reload(ls_module)
    
    service = ls_module.LLMService()
    
    # Test finding existing model
    config = service._get_config("gpt-4")
    assert config.id == "gpt-4"
    assert config.provider == "openai"
    
    # Test invalid
    with pytest.raises(ValueError):
        service._get_config("non-existent-model-id-999")
