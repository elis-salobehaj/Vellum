import pytest
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
    """Verify AWS Credentials are loaded."""
    if not settings.AWS_ACCESS_KEY_ID:
        pytest.skip("AWS_ACCESS_KEY_ID not set")

    assert settings.AWS_SECRET_ACCESS_KEY, "AWS_SECRET_ACCESS_KEY missing"
    assert settings.AWS_REGION, "AWS_REGION missing"

    # Minimal check: Can we instantiate the client without error?
    try:
        import boto3

        session = boto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        # Check if bedrock service is available in region
        assert "bedrock-runtime" in session.get_available_services()
    except ImportError:
        pytest.fail("boto3 not installed")
