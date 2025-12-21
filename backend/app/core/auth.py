from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings

# In a real Entra ID setup, this would point to the token endpoint
# auto_error=False allows us to handle the missing token manually (or bypass it)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Validates the separate access token from Entra ID.
    If BYPASS_AUTH is True, we skip validation and return a mock user.
    """
    if settings.BYPASS_AUTH:
        return {"token": "bypass-token", "user": "bypassed-user", "roles": ["admin"]}
        
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # TODO: Implement JWT validation using python-jose and JWKS
    return {"token": token, "user": "test-user"}
