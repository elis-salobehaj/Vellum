import os

os.environ["BYPASS_AUTH"] = "true"

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from main import app
from app.api.endpoints.admin import MODEL_CONFIGS
from app.core.auth import get_current_user

client = TestClient(app)
app.dependency_overrides[get_current_user] = lambda: {"user": "test-user"}


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Vellum API"}


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    # The actual endpoint returns {"status": "healthy"}
    assert response.json() == {"status": "healthy"}


@patch("app.api.endpoints.chat.rag_service.query", new_callable=AsyncMock)
@patch("app.api.endpoints.chat.llm_service.chat", new_callable=AsyncMock)
@patch("app.services.history_service.history_service.get_messages")
def test_chat_endpoint(mock_get_msgs, mock_chat, mock_query):
    # Mock the service layer functions that the endpoint calls
    mock_query.return_value = [
        {
            "text": "context",
            "metadata": {"file_name": "test.pdf", "page_label": "1"},
            "score": 0.9,
        }
    ]
    mock_chat.return_value = "Test response"
    mock_get_msgs.return_value = []

    # Payload includes new fields
    response = client.post(
        "/api/v1/chat",
        json={"message": "Hello", "context_window": 3, "model_id": "gpt-4"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Test response"
    assert len(data["citations"]) == 1
    assert (
        data["session_id"] is not None
    )  # Endpoint should generate one if not provided

    mock_chat.assert_called_once()
    mock_query.assert_called_with("Hello", k=3)


@patch("app.api.endpoints.chat.rag_service.query", new_callable=AsyncMock)
@patch("app.api.endpoints.chat.llm_service.chat", new_callable=AsyncMock)
def test_chat_no_context(mock_chat, mock_query):
    # Test chat when RAG returns no context
    mock_query.return_value = []
    mock_chat.return_value = "I don't know based on the context."

    response = client.post("/api/v1/chat", json={"message": "What is life?"})

    assert response.status_code == 200
    assert response.json()["response"] == "I don't know based on the context."
    assert response.json()["citations"] == []


@patch("app.api.endpoints.chat.rag_service.query", new_callable=AsyncMock)
@patch("app.api.endpoints.chat.llm_service.chat", new_callable=AsyncMock)
def test_chat_llm_error(mock_chat, mock_query):
    # Test chat when LLM service fails
    mock_query.return_value = []
    mock_chat.side_effect = Exception("LLM connection failed")

    with pytest.raises(
        Exception
    ):  # FastAPI will propagate or catch depending on config
        response = client.post("/api/v1/chat", json={"message": "Hello"})
        # If we don't have a middlewae catching this, it might be 500
        assert response.status_code == 500


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
        "model_api_path": "test-model-custom",
        "name": "Test Model",
        "provider": "ollama",
        "is_active": True,
    }

    try:
        response = client.post("/api/v1/admin/models", json=new_model)
        assert response.status_code == 200
        assert response.json()["id"] == "test-model-custom"
        assert response.json()["model_api_path"] == "test-model-custom"

        # 3. Verify
        response = client.get("/api/v1/admin/models")
        assert len(response.json()) == original_len + 1

        # 4. Update using the API path route contract
        updated_model = {
            **new_model,
            "name": "Updated Test Model",
            "is_active": False,
        }
        response = client.put(
            "/api/v1/admin/models/test-model-custom",
            json=updated_model,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Test Model"

        # 5. Duplicate
        response = client.post("/api/v1/admin/models", json=new_model)
        assert response.status_code == 400

    finally:
        # Cleanup: remove the added model
        MODEL_CONFIGS[:] = [m for m in MODEL_CONFIGS if m.id != "test-model-custom"]


@patch("app.services.history_service.history_service.get_recent_conversations")
@patch("app.services.history_service.history_service.get_messages")
def test_history_endpoints(mock_get_msgs, mock_get_recent):
    mock_get_recent.return_value = [
        {"id": "1", "title": "Test Chat", "date": "2023-01-01"}
    ]
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


@patch("app.services.direct_ingestion_service.direct_ingestion_service.get_status")
def test_admin_ingestion_status(mock_get_status):
    mock_get_status.return_value = {
        "status": "paused",
        "bucket_object_count": 105,
        "indexed_source_doc_count": 50,
        "current_file": "docs/example.pdf",
        "recent_skipped_files": ["docs/unsupported.ppt"],
    }

    response = client.get("/api/v1/admin/ingestion-status")

    assert response.status_code == 200
    assert response.json()["status"] == "paused"
    assert response.json()["bucket_object_count"] == 105
    assert response.json()["indexed_source_doc_count"] == 50


@patch("app.services.direct_ingestion_service.direct_ingestion_service.get_status")
@patch("app.services.direct_ingestion_service.direct_ingestion_service.run")
def test_admin_upload_and_ingest_passes_cleanup_and_reports_status(
    mock_run, mock_get_status
):
    mock_run.return_value = ["✅ Direct ingestion complete"]
    mock_get_status.return_value = {
        "status": "completed",
        "bucket_object_count": 10,
        "indexed_source_doc_count": 9,
        "pending_source_object_count": 1,
        "recent_skipped_files": ["docs/unsupported.ppt"],
    }

    with patch("app.api.endpoints.admin.settings.INGESTION_MODE", "direct"):
        with patch("app.api.endpoints.admin.os.path.exists", return_value=True):
            with patch("app.api.endpoints.admin.os.listdir", return_value=[]):
                with patch("app.api.endpoints.admin.Minio") as mock_minio:
                    mock_minio.return_value.bucket_exists.return_value = True
                    response = client.post(
                        "/api/v1/admin/upload-and-ingest?batch_size=20&reset_progress=true&cleanup=true"
                    )

    assert response.status_code == 200
    mock_run.assert_called_once_with(
        bucket="documents",
        cleanup=True,
        batch_size=20,
        reset_progress=True,
    )
    assert "Clean-slate ingestion requested" in response.text
    assert "Status: 9/10 indexed" in response.text
    assert "docs/unsupported.ppt" in response.text
