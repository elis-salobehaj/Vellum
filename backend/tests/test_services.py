import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.history_service import HistoryService
from app.services.llm_service import LLMService
from app.models.schemas import ModelConfig

@pytest.fixture
def history_service():
    # Use a fresh instance of HistoryService
    return HistoryService()

@pytest.fixture
def ll_service():
    # Mock llama_index dependencies globally in conftest.py helps here
    return LLMService()

def test_history_service_add_message(history_service):
    # Patch the global STORAGE to isolate test if needed, 
    # but since it's an instance, we can just test it.
    # Actually, if HistoryService uses a global variable, we patch it in the module.
    with patch("app.services.history_service.CONVERSATIONS", {}):
        history_service.add_message("sess-123", "user", "Hello Vellum")
        
        messages = history_service.get_messages("sess-123")
        assert len(messages) == 1
        assert messages[0]["content"] == "Hello Vellum"
        assert messages[0]["role"] == "user"

def test_history_service_get_recent(history_service):
    with patch("app.services.history_service.CONVERSATIONS", {}):
        history_service.add_message("s1", "user", "Chat 1")
        history_service.add_message("s1", "assistant", "Response 1")
        history_service.add_message("s2", "user", "Chat 2")
        
        recent = history_service.get_recent_conversations("default")
        assert len(recent) == 2
        # Verify order/content
        assert any(r["id"] == "s1" for r in recent)
        assert any(r["id"] == "s2" for r in recent)

@pytest.mark.asyncio
async def test_llm_service_openai(ll_service):
    # The OpenAI class is imported at the top of llm_service.py
    config = ModelConfig(id="gpt-4", name="GPT4", provider="openai", api_key="sk-test")
    
    # Patch where it's used (in the llm_service module)
    with patch("app.services.llm_service.OpenAI") as mock_openai:
        await ll_service._get_llm(config)
        assert mock_openai.called
        # The actual call includes api_base parameter
        mock_openai.assert_called_with(
            model="gpt-4", 
            api_key="sk-test", 
            api_base="https://api.openai.com/v1"
        )

@pytest.mark.asyncio
async def test_llm_service_google(ll_service):
    config = ModelConfig(id="gemini-1.5", name="Gemini", provider="google")
    
    # Patch where it's imported (inside the method)
    with patch("llama_index.llms.gemini.Gemini") as mock_gemini:
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "fake-key"}):
            await ll_service._get_llm(config)
            assert mock_gemini.called
            mock_gemini.assert_called_with(model="models/gemini-1.5", api_key="fake-key")

@pytest.mark.asyncio
async def test_llm_service_kubeflow(ll_service):
    config = ModelConfig(id="qwen", name="Qwen", provider="kubeflow", base_url="http://kfp:80")
    
    # Patch where it's imported (inside the method)
    with patch("llama_index.llms.openai_like.OpenAILike") as mock_openai_like:
        await ll_service._get_llm(config)
        assert mock_openai_like.called
        mock_openai_like.assert_called_with(
            model="qwen",
            api_base="http://kfp:80",
            api_key="dummy",
            is_chat_model=True,
            max_tokens=2048
        )

@pytest.mark.asyncio
async def test_llm_service_invalid_provider(ll_service):
    config = ModelConfig(id="bad", name="bad", provider="unknown")
    with pytest.raises(ValueError) as exc:
        await ll_service._get_llm(config)
    # The actual error message is "Provider unknown not supported."
    assert "not supported" in str(exc.value)
