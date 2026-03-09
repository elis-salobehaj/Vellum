import pytest
from unittest.mock import patch

from app.core.config import settings


@pytest.mark.asyncio
async def test_openai_connectivity():
    """Verify OpenAI API Key is loaded and potentially works."""
    assert settings.OPENAI_API_KEY, "OPENAI_API_KEY is not set in config/env"

    # Optional: Actual call if we wanted to verify cost (not doing it in CI)
    # from langchain_openai import ChatOpenAI
    # llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY)
    # res = await llm.ainvoke("Hello")
    # assert res.content


@pytest.mark.asyncio
async def test_aws_bedrock_connectivity():
    """Verify Bedrock API-key connectivity is configured and usable."""
    if not settings.AWS_BEDROCK_API_KEY:
        pytest.skip("AWS_BEDROCK_API_KEY not set")

    assert settings.AWS_REGION, "AWS_REGION missing"

    try:
        import boto3

        with patch.dict(
            "os.environ",
            {"AWS_BEARER_TOKEN_BEDROCK": settings.AWS_BEDROCK_API_KEY},
            clear=False,
        ):
            client = boto3.client("bedrock", region_name=settings.AWS_REGION)
            response = client.list_foundation_models(byProvider="Anthropic")

        assert response.get("modelSummaries"), "No Anthropic Bedrock models returned"
    except ImportError:
        pytest.fail("boto3 not installed")
