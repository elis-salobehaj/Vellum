import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.dagster_service import DagsterService, _LAUNCH_MUTATION

@pytest.mark.asyncio
async def test_trigger_ingestion_success():
    service = DagsterService()
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "launchPipelineExecution": {
                "__typename": "LaunchRunSuccess",
                "run": {"runId": "12345"}
            }
        }
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
        result = await service.trigger_ingestion()
        
    assert result == {
        "status": "success",
        "run_id": "12345",
        "message": "Dagster ingestion job launched. Run ID: 12345",
    }
    
    # Assert headers and payload were correct
    mock_post.assert_called_with(
        service.graphql_url,
        json={"query": _LAUNCH_MUTATION},
        headers={"Content-Type": "application/json"}
    )

@pytest.mark.asyncio
async def test_trigger_ingestion_error():
    service = DagsterService()
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "launchPipelineExecution": {
                "__typename": "PythonError",
                "message": "Division by zero"
            }
        }
    }
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        result = await service.trigger_ingestion()
        
    assert result == {
        "status": "error",
        "message": "Division by zero"
    }

@pytest.mark.asyncio
async def test_trigger_ingestion_http_exception():
    service = DagsterService()
    
    with patch("httpx.AsyncClient.post", side_effect=Exception("Connection Refused")):
        result = await service.trigger_ingestion()
        
    assert result == {
        "status": "error",
        "message": "Connection Refused"
    }
