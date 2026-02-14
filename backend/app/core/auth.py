from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import requests
from app.core.config import settings
from functools import lru_cache

# In a real Entra ID setup, this would point to the token endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

@lru_cache()
def get_jwks():
    """Fetch and cache Azure JWKS."""
    # We use the tenant-specific endpoint for better security
    jwks_uri = f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/discovery/v2.0/keys"
    return requests.get(jwks_uri).json()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    userid_header: str | None = Header(None, alias="kubeflow-userid")
):
    """
    Validates either a Bearer token (Entra ID) or a kubeflow-userid header (Istio/Dex).
    """
    if settings.BYPASS_AUTH:
        print("DEBUG: Auth bypassed via settings.")
        return {"token": "bypass-token", "user": "bypassed-user", "roles": ["admin"]}

    # 1. Check for Kubeflow header (internal gateway auth)
    if userid_header:
        print(f"DEBUG: Authenticated via Kubeflow header: {userid_header}")
        return {
            "token": None,
            "user": userid_header,
            "roles": ["admin"] # Default to admin for now in multi-user
        }
        
    if not token or token == "mock-token":
        print(f"DEBUG: Missing or mock token: {token}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # 1. Get header to find kid
        unverified_header = jwt.get_unverified_header(token)
        print(f"DEBUG: Validating Azure token for client {settings.AZURE_CLIENT_ID}")
        
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
            print(f"DEBUG: kid {unverified_header.get('kid')} not found in JWKS")
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
            print(f"DEBUG: Invalid audience: {aud}. Expected one of: {allowed_auds}")
            raise JWTError(f"Invalid audience: {aud}")
        
        user_id = payload.get("preferred_username") or payload.get("sub")
        print(f"DEBUG: Azure token validated for user: {user_id}")
        return {
            "token": token,
            "user": user_id,
            "payload": payload
        }
    except JWTError as e:
        print(f"DEBUG: JWT Error: {str(e)}")
        try:
            unverified_claims = jwt.get_unverified_claims(token)
            unverified_header = jwt.get_unverified_header(token)
            print(f"DEBUG: Unverified Header: {unverified_header}")
            print(f"DEBUG: Unverified Claims: {unverified_claims}")
        except:
            print("DEBUG: Could not even parse unverified claims.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        print(f"DEBUG: Unexpected Auth Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
