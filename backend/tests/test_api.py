import sys
from unittest.mock import MagicMock, AsyncMock

# Mock heavy dependencies BEFORE importing main to avoid model downloads
mock_rag_service = MagicMock()
mock_rag_service.rag_service = MagicMock()
mock_rag_service.rag_service.query = AsyncMock(return_value=[])
sys.modules["app.services.rag_service"] = mock_rag_service

mock_llm_service = MagicMock()
mock_llm_service.llm_service = MagicMock()
mock_llm_service.llm_service.generate_response = AsyncMock(return_value="Mocked Response")
sys.modules["app.services.llm_service"] = mock_llm_service

# Mock history service
mock_history_service = MagicMock()
mock_history_service.history_service = MagicMock()
mock_history_service.history_service.get_messages.return_value = []
sys.modules["app.services.history_service"] = mock_history_service

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Vellum API"}

def test_health_check():
    response = client.get("/health")
    # Health check doesn't use services, so it should pass
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_chat_endpoint():
    response = client.post("/api/v1/chat", json={"message": "Hello", "model_id": "mistral"})
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Mocked Response"
    assert "session_id" in data

