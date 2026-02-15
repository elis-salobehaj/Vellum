from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import requests
from app.core.config import settings
from app.core.logging import logger
from functools import lru_cache

# In a real Entra ID setup, this would point to the token endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

@lru_cache()
def get_jwks():
    """Fetch and cache Azure JWKS."""
    # We use the tenant-specific endpoint for better security
    jwks_uri = f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/discovery/v2.0/keys"
    try:
        response = requests.get(jwks_uri)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("auth_jwks_fetch_failed", error=str(e), uri=jwks_uri)
        raise

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    userid_header: str | None = Header(None, alias="kubeflow-userid")
):
    """
    Validates either a Bearer token (Entra ID) or a kubeflow-userid header (Istio/Dex).
    """
    if settings.BYPASS_AUTH:
        logger.warning("auth_bypassed", user="bypassed-user")
        return {"token": "bypass-token", "user": "bypassed-user", "roles": ["admin"]}

    # 1. Check for Kubeflow header (internal gateway auth)
    # When called in tests directly, userid_header may be the Header() object.
    if userid_header and isinstance(userid_header, str):
        logger.info("auth_header_success", user=userid_header, provider="kubeflow")
        return {
            "token": None,
            "user": userid_header,
            "roles": ["admin"] # Default to admin for now in multi-user
        }
        
    if not token or token == "mock-token":
        logger.warning("auth_token_missing", token_provided=bool(token))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # 1. Get header to find kid
        unverified_header = jwt.get_unverified_header(token)
        logger.debug("auth_validating_token", client_id=settings.AZURE_CLIENT_ID, kid=unverified_header.get("kid"))
        
        # 2. Get JWKS
        jwks = get_jwks()
        
        # 3. Find correct key
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break
        
        if not rsa_key:
            logger.error("auth_kid_not_found", kid=unverified_header.get('kid'))
            raise HTTPException(status_code=401, detail="Invalid token header (kid not found)")

        # 4. Validate Token
        # Audience should be our Client ID.
        # Azure sometimes uses api://<client_id> for access tokens.
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            options={
                "verify_aud": False, 
                "verify_issuer": False
            }
        )
        
        # Manual Audience Check
        aud = payload.get("aud")
        allowed_auds = [settings.AZURE_CLIENT_ID, f"api://{settings.AZURE_CLIENT_ID}"]
        if aud not in allowed_auds:
            logger.error("auth_invalid_audience", audience=aud, expected=allowed_auds)
            raise JWTError(f"Invalid audience: {aud}")
        
        user_id = payload.get("preferred_username") or payload.get("sub")
        logger.info("auth_token_success", user=user_id, provider="azure_ad")
        return {
            "token": token,
            "user": user_id,
            "payload": payload
        }
    except JWTError as e:
        logger.error("auth_jwt_error", error=str(e))
        try:
            unverified_claims = jwt.get_unverified_claims(token)
            unverified_header = jwt.get_unverified_header(token)
            logger.debug("auth_jwt_debug", header=unverified_header, claims=unverified_claims)
        except:
            pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error("auth_unexpected_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
