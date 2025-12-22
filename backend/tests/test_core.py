from app.core.config import settings
from app.core.auth import get_current_user
import pytest

def test_config_values():
    assert settings.PROJECT_NAME == "Vellum"
    assert settings.API_V1_STR == "/api/v1"

@pytest.mark.asyncio
async def test_auth_logic():
    # If BYPASS_AUTH is enabled in test environment
    if settings.BYPASS_AUTH:
        user = await get_current_user("dummy_token")
        assert user["user"] == "bypassed-user"
        assert "admin" in user["roles"]
