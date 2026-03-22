"""Backend authentication — Entra ID JWT (primary) only.

The previous kubeflow-userid header fallback has been removed as of Phase 4.
Dex / oauth2-proxy are no longer part of the stack, so that header path was
a spoofable auth bypass. The only valid auth paths now are:

  1. Bearer token (Entra ID / Azure AD JWT) — production
  2. BYPASS_AUTH=true — local developer override

Istio Ambient (L7 AuthorizationPolicy) still validates the JWT at the mesh
layer before requests reach the backend, providing a defense-in-depth second
layer for any path that reaches the service at all.
"""

from functools import lru_cache

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import settings
from app.core.logging import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


@lru_cache()
def get_jwks() -> dict:
    """Fetch and cache Azure JWKS (v2.0 common)."""
    jwks_uri = "https://login.microsoftonline.com/common/discovery/v2.0/keys"
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(jwks_uri)
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        logger.error("auth_jwks_fetch_failed", error=str(exc), uri=jwks_uri)
        raise HTTPException(status_code=500, detail="Could not fetch Azure JWKS") from exc


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> dict:
    """
    Validate an Entra ID Bearer token.

    Returns a dict with keys: token, user, roles (or payload for full claims).
    Raises HTTP 401 for any invalid or missing token.
    """
    if settings.BYPASS_AUTH:
        logger.warning("auth_bypassed", user="bypassed-user")
        return {"token": "bypass-token", "user": "bypassed-user", "roles": ["admin"]}

    if not token or token == "mock-token":
        logger.warning("auth_token_missing", token_provided=bool(token))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        unverified_header = jwt.get_unverified_header(token)
        logger.debug(
            "auth_validating_token",
            client_id=settings.AZURE_CLIENT_ID,
            kid=unverified_header.get("kid"),
        )

        jwks = get_jwks()

        rsa_key: dict = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
                break

        if not rsa_key:
            logger.error("auth_kid_not_found", kid=unverified_header.get("kid"))
            raise HTTPException(status_code=401, detail="Invalid token header (kid not found)")

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            options={"verify_aud": False, "verify_issuer": False},
        )

        aud = payload.get("aud")
        allowed_auds = [settings.AZURE_CLIENT_ID, f"api://{settings.AZURE_CLIENT_ID}"]
        if aud not in allowed_auds:
            logger.error("auth_invalid_audience", audience=aud, expected=allowed_auds)
            raise JWTError(f"Invalid audience: {aud}")

        user_id = payload.get("preferred_username") or payload.get("sub")
        logger.info("auth_token_success", user=user_id, provider="azure_ad")
        return {"token": token, "user": user_id, "payload": payload}

    except HTTPException:
        raise
    except JWTError as exc:
        logger.error("auth_jwt_error", error=str(exc))
        try:
            unverified_claims = jwt.get_unverified_claims(token)
            logger.debug("auth_jwt_debug", claims=unverified_claims)
        except Exception:  # noqa: BLE001
            pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except Exception as exc:
        logger.error("auth_unexpected_error", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc
