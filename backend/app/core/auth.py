"""
Authentication Module - Firebase Auth Token Verification

Provides dependency injection for FastAPI endpoints to verify Firebase Auth tokens.
"""

from dataclasses import dataclass
from typing import Any

from fastapi import Depends, Header, HTTPException, status
from firebase_admin import auth

from app.core.logging import logger

DEMO_WORKSPACE_ID = "__shared_ingen_demo_v1__"


@dataclass(frozen=True)
class FirebasePrincipal:
    """Identity facts derived only from a verified Firebase ID token."""

    uid: str
    is_anonymous: bool


@dataclass(frozen=True)
class WorkspaceAccess:
    """Authorized workspace selected for one authenticated principal."""

    principal_uid: str
    workspace_id: str
    is_guest: bool


def firebase_principal_from_claims(decoded_token: dict[str, Any]) -> FirebasePrincipal:
    firebase_claims = decoded_token.get("firebase")
    provider = (
        firebase_claims.get("sign_in_provider")
        if isinstance(firebase_claims, dict)
        else None
    )
    return FirebasePrincipal(
        uid=str(decoded_token["uid"]),
        is_anonymous=provider == "anonymous",
    )


def verify_firebase_principal(authorization: str = Header(None)) -> FirebasePrincipal:
    """
    Verify Firebase Auth token from Authorization header.

    Args:
        authorization: Authorization header in format "Bearer <token>"

    Returns:
        str: Verified user ID (uid) from token

    Raises:
        HTTPException: 401 if token is missing, invalid, or expired

    Usage:
        @router.post("/endpoint/")
        async def protected_endpoint(
            user_id: str = Depends(verify_firebase_token),
            ...
        ):
    """
    # Check if Authorization header exists
    if not authorization:
        logger.warning("⚠️ Missing Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header. Please provide a valid Firebase Auth token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if header has correct format
    if not authorization.startswith("Bearer "):
        logger.warning("Invalid Authorization header format")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected: 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token
    token = authorization.split("Bearer ")[1].strip()

    if not token:
        logger.warning("⚠️ Empty token in Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token with Firebase Admin SDK
    try:
        decoded_token = auth.verify_id_token(token)
        principal = firebase_principal_from_claims(decoded_token)
        logger.debug("Firebase token verified")
        return principal

    except auth.ExpiredIdTokenError:
        logger.warning("⚠️ Expired Firebase token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase token has expired. Please refresh your authentication.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except auth.RevokedIdTokenError:
        logger.warning("⚠️ Revoked Firebase token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase token has been revoked. Please re-authenticate.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except auth.InvalidIdTokenError:
        logger.warning("⚠️ Invalid Firebase token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token. Please re-authenticate.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except Exception as exc:
        logger.error("Unexpected token-verification failure | Type: {}", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed. Please try again.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def verify_firebase_token(authorization: str = Header(None)) -> str:
    """Return the UID from the existing verified-token boundary."""
    return verify_firebase_principal(authorization).uid


def get_workspace_access(
    principal: FirebasePrincipal = Depends(verify_firebase_principal),
) -> WorkspaceAccess:
    """Map guests to the shared corpus and registered users to their private UID."""
    return WorkspaceAccess(
        principal_uid=principal.uid,
        workspace_id=DEMO_WORKSPACE_ID if principal.is_anonymous else principal.uid,
        is_guest=principal.is_anonymous,
    )


def require_registered_user(
    principal: FirebasePrincipal = Depends(verify_firebase_principal),
) -> str:
    """Reject anonymous identities on every mutation/account boundary."""
    if principal.is_anonymous:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guest workspaces are read-only.",
        )
    return principal.uid


def require_verified_registered_user(
    principal: FirebasePrincipal = Depends(verify_firebase_principal),
) -> str:
    """Require a non-anonymous Firebase user with a verified email."""
    user_id = require_registered_user(principal)
    return require_verified_email(user_id)


def get_query_workspace_access(
    access: WorkspaceAccess = Depends(get_workspace_access),
) -> WorkspaceAccess:
    """Allow guests to query the demo and require verified email otherwise."""
    if not access.is_guest:
        require_verified_email(access.principal_uid)
    return access


def get_verified_user_id(authorization: str = Header(None)) -> str:
    """
    Alias for verify_firebase_token for better semantic clarity.

    Usage:
        user_id: str = Depends(get_verified_user_id)
    """
    return verify_firebase_token(authorization)


def require_verified_email(
    user_id: str = Depends(verify_firebase_token),
) -> str:
    """Require a verified Firebase email before starting expensive work.

    The UID is still derived only from the verified Firebase token.  Looking up
    the Firebase user record keeps this guard compatible with the existing UID
    dependency while using Firebase's authoritative verification state.
    """
    try:
        user = auth.get_user(user_id)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("⚠️ Unable to verify email status for authenticated user")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A verified email address is required for this operation.",
        ) from exc

    if not bool(getattr(user, "email_verified", False)):
        logger.info("⛔ Expensive operation rejected for unverified Firebase email")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address before using this feature.",
        )

    return user_id
