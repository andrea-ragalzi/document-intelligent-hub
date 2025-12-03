"""
Authentication Module - Firebase Auth Token Verification

Provides dependency injection for FastAPI endpoints to verify Firebase Auth tokens.
"""

from app.core.logging import logger
from fastapi import Header, HTTPException, status
from firebase_admin import auth


def verify_firebase_token(authorization: str = Header(None)) -> str:
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
        logger.warning(
            f"⚠️ Invalid Authorization header format: {authorization[:20]}..."
        )
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
        user_id = str(decoded_token["uid"])

        # Optional: Log successful authentication (verbose mode only)
        logger.debug(f"✅ Token verified for user: {user_id}")

        return user_id

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

    except Exception as e:
        logger.error(f"❌ Unexpected error verifying token: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed. Please try again.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_verified_user_id(authorization: str = Header(None)) -> str:
    """
    Alias for verify_firebase_token for better semantic clarity.

    Usage:
        user_id: str = Depends(get_verified_user_id)
    """
    return verify_firebase_token(authorization)
