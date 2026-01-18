import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from main import app
from app.api.endpoints.admin import MODEL_CONFIGS

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Vellum API"}

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@patch("app.api.endpoints.chat.rag_service.query", new_callable=AsyncMock)
@patch("app.api.endpoints.chat.llm_service.chat", new_callable=AsyncMock)
@patch("app.services.history_service.history_service.get_messages")
def test_chat_endpoint(mock_get_msgs, mock_chat, mock_query):
    # Mock the service layer functions that the endpoint calls
    mock_query.return_value = [{"text": "context", "metadata": {"file_name": "test.pdf", "page_label": "1"}, "score": 0.9}]
    mock_chat.return_value = "Test response"
    mock_get_msgs.return_value = [] 

    # Payload includes new fields
    response = client.post("/api/v1/chat", json={
        "message": "Hello", 
        "context_window": 3,
        "model_id": "gpt-4"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Test response"
    assert len(data["citations"]) == 1
    assert data["session_id"] is None # Should NOT generate a new one if not provided
    
    mock_chat.assert_called_once()
    mock_query.assert_called_with("Hello", k=3)

def test_chat_validation_error():
    # Missing message is 422
    response = client.post("/api/v1/chat", json={"context_window": 5})
    # Only context_window provided, message missing -> 422
    assert response.status_code == 422

def test_admin_models_crud():
    original_len = len(MODEL_CONFIGS)
    
    # 1. GET
    response = client.get("/api/v1/admin/models")
    assert response.status_code == 200
    assert len(response.json()) == original_len
    
    # 2. POST
    new_model = {
        "id": "test-model-custom",
        "name": "Test Model",
        "provider": "ollama",
        "is_active": True
    }
    
    try:
        response = client.post("/api/v1/admin/models", json=new_model)
        assert response.status_code == 200
        assert response.json()["id"] == "test-model-custom"
        
        # 3. Verify
        response = client.get("/api/v1/admin/models")
        assert len(response.json()) == original_len + 1
        
        # 4. Duplicate
        response = client.post("/api/v1/admin/models", json=new_model)
        assert response.status_code == 400
        
    finally:
        # Cleanup: remove the added model
        MODEL_CONFIGS[:] = [m for m in MODEL_CONFIGS if m.id != "test-model-custom"]

@patch("app.services.history_service.history_service.get_recent_conversations")
@patch("app.services.history_service.history_service.get_messages")
def test_history_endpoints(mock_get_msgs, mock_get_recent):
    mock_get_recent.return_value = [{"id": "1", "title": "Test Chat", "date": "2023-01-01"}]
    mock_get_msgs.return_value = []
    
    # 1. GET Recent
    response = client.get("/api/v1/history/")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Test Chat"
    
    # 2. GET Session
    response = client.get("/api/v1/history/session_123")
    assert response.status_code == 200
    assert response.json() == []
