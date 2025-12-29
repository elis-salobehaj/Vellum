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

# Mock get_recent_conversations for history test
mock_history_service.history_service.get_recent_conversations.return_value = [
    {"id": "1", "title": "Test Chat", "date": "2023-01-01"}
]


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

def test_chat_validation_error():
    # Missing required message field
    response = client.post("/api/v1/chat", json={"model_id": "mistral"})
    assert response.status_code == 422

def test_admin_models_crud():
    # 1. GET Models
    response = client.get("/api/v1/admin/models")
    assert response.status_code == 200
    models = response.json()
    assert isinstance(models, list)
    assert len(models) >= 1
    
    # 2. POST New Model
    new_model_id = "test-model-custom"
    new_model = {
        "id": new_model_id,
        "name": "Test Model",
        "provider": "ollama",
        "is_active": True
    }
    response = client.post("/api/v1/admin/models", json=new_model)
    assert response.status_code == 200
    created = response.json()
    assert created["id"] == new_model_id
    assert created["is_active"] is True

    # 3. Verify it appears in list and active state
    response = client.get("/api/v1/admin/models")
    models = response.json()
    model_obj = next((m for m in models if m["id"] == new_model_id), None)
    assert model_obj is not None
    assert model_obj["is_active"] is True

    # 4. Error on Duplicate
    response = client.post("/api/v1/admin/models", json=new_model)
    assert response.status_code == 400

def test_history_endpoints():
    # 1. GET Recent History
    response = client.get("/api/v1/history/")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 1
    assert history[0]["title"] == "Test Chat"

    # 2. GET Specific Session (mocked to return empty list messages)
    response = client.get("/api/v1/history/session_123")
    assert response.status_code == 200
    assert response.json() == []

