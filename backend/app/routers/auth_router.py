"""
Authentication Router

Handles user registration and tier assignment via Firebase Custom Claims.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

from app.core.logging import logger
from app.schemas.auth_schema import (
    InvitationCodeRequest,
    InvitationCodeRequestResponse,
    RegistrationData,
    RegistrationResponse,
)
from app.services.email_service import get_email_service
from app.services.usage_tracking_service import get_usage_service
from fastapi import APIRouter, Depends, Header, HTTPException
from firebase_admin import auth, firestore
from google.cloud.firestore import SERVER_TIMESTAMP

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_db() -> Any:
    """Get or initialize Firestore client (lazy initialization using function attribute)."""
    if not hasattr(get_db, "client"):
        get_db.client = firestore.client()  # type: ignore[attr-defined]
    return get_db.client  # type: ignore[attr-defined]


def calculate_remaining_queries(query_limit: int, queries_used: int) -> int:
    """
    Calculate remaining queries for a user.

    For UNLIMITED tier (query_limit=9999), returns -1 as a special indicator.
    For other tiers, returns the actual remaining count.

    Args:
        query_limit: Maximum queries allowed per day
        queries_used: Number of queries already used today

    Returns:
        int: Remaining queries (-1 for UNLIMITED, actual count for other tiers)

    Examples:
        >>> calculate_remaining_queries(20, 15)
        5
        >>> calculate_remaining_queries(9999, 5000)
        -1
    """
    unlimited_threshold = 9999
    unlimited_indicator = -1

    if query_limit == unlimited_threshold:
        return unlimited_indicator

    return max(0, query_limit - queries_used)


def get_current_user_id(authorization: str = Header(...)) -> str:
    """
    Extract and validate user ID from Firebase token.

    Args:
        authorization: Bearer token from Authorization header

    Returns:
        str: Validated user ID

    Raises:
        HTTPException: If token is invalid or missing
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid authorization header"
        )

    token = authorization.replace("Bearer ", "")

    try:
        decoded_token = auth.verify_id_token(token)
        user_id = str(decoded_token["uid"])
        return user_id
    except Exception as e:
        logger.error(f"❌ Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token") from e


def clear_cache() -> None:
    """
    Clear the application configuration cache.

    Useful for testing to ensure fresh data is loaded from Firestore.
    """
    if hasattr(load_app_config, "unlimited_emails_cache"):
        delattr(load_app_config, "unlimited_emails_cache")
    if hasattr(load_app_config, "tier_limits_cache"):
        delattr(load_app_config, "tier_limits_cache")


def load_app_config() -> dict[str, Any]:
    """
    Load application configuration from Firestore app_config/settings.

    Returns a dictionary with:
    - unlimited_emails: List[str]
    - limits: dict with tier limits (FREE, PRO, UNLIMITED)

    UNLIMITED tier limits are always injected with max values (9999).
    Results are cached to reduce Firestore reads.
    """
    # Return cached values if available
    if hasattr(load_app_config, "unlimited_emails_cache") and hasattr(
        load_app_config, "tier_limits_cache"
    ):
        return {
            "unlimited_emails": load_app_config.unlimited_emails_cache,  # type: ignore
            "limits": load_app_config.tier_limits_cache,  # type: ignore[attr-defined]
        }

    try:
        db = get_db()
        settings_ref = db.collection("app_config").document("settings")
        settings_doc = settings_ref.get()

        if settings_doc.exists:
            data = settings_doc.to_dict()
            if data:
                # Extract configuration
                unlimited_emails = data.get("unlimited_emails", [])
                tier_limits = data.get("limits", {})

                # Always inject UNLIMITED tier with max values
                tier_limits["UNLIMITED"] = {
                    "max_queries_per_day": 9999,
                    "max_files": 9999,
                    "max_file_size_mb": 9999,
                }

                # Cache results (using function attributes for singleton pattern)
                load_app_config.unlimited_emails_cache = unlimited_emails  # type: ignore
                load_app_config.tier_limits_cache = tier_limits  # type: ignore

                logger.info(
                    f"✅ Loaded app config: "
                    f"{len(unlimited_emails)} unlimited emails, "
                    f"{len(tier_limits)} tier limits"
                )
                return {"unlimited_emails": unlimited_emails, "limits": tier_limits}

        # Document not found, use defaults
        logger.warning("⚠️ app_config/settings not found, using defaults")
        default_unlimited: List[str] = []
        default_limits = {
            "FREE": {"max_queries_per_day": 20, "max_files": 5, "max_file_size_mb": 10},
            "PRO": {
                "max_queries_per_day": 500,
                "max_files": 50,
                "max_file_size_mb": 50,
            },
            "UNLIMITED": {
                "max_queries_per_day": 9999,
                "max_files": 9999,
                "max_file_size_mb": 9999,
            },
        }
        return {"unlimited_emails": default_unlimited, "limits": default_limits}

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"❌ Error loading app config: {e}")
        return {
            "unlimited_emails": [],
            "limits": {
                "FREE": {
                    "max_queries_per_day": 20,
                    "max_files": 5,
                    "max_file_size_mb": 10,
                },
                "PRO": {
                    "max_queries_per_day": 500,
                    "max_files": 50,
                    "max_file_size_mb": 50,
                },
                "UNLIMITED": {
                    "max_queries_per_day": 9999,
                    "max_files": 9999,
                    "max_file_size_mb": 9999,
                },
            },
        }


def get_unlimited_emails() -> List[str]:
    """
    Retrieve list of emails with unlimited tier access from Firestore.

    Fetches from app_config/settings document and caches result.
    Falls back to empty list if document not found or error occurs.

    Returns:
        List of email addresses with unlimited access
    """
    # Return cached value if available
    if hasattr(get_unlimited_emails, "cache"):
        return list(get_unlimited_emails.cache)  # type: ignore[attr-defined,no-any-return]

    try:
        # Fetch settings document from Firestore
        db = get_db()
        settings_ref = db.collection("app_config").document("settings")
        settings_doc = settings_ref.get()

        if settings_doc.exists:
            data = settings_doc.to_dict()
            if data:  # Check data is not None
                unlimited_emails = data.get("unlimited_emails", [])

                # Validate that it's a list
                if isinstance(unlimited_emails, list):
                    get_unlimited_emails.cache = unlimited_emails  # type: ignore[attr-defined]
                    logger.info(
                        f"✅ Loaded {len(unlimited_emails)} unlimited emails from Firestore"
                    )
                    return unlimited_emails

        # Document not found or invalid format
        logger.warning(
            "⚠️ app_config/settings not found or invalid format, using empty list"
        )
        get_unlimited_emails.cache = []  # type: ignore[attr-defined]
        return []

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"❌ Error fetching unlimited emails: {e}")
        # Fallback to empty list on error
        return []


def _verify_token_and_get_user_info(id_token: str) -> tuple[str, str | None]:
    """
    Verify Firebase ID token and extract user info.

    Args:
        id_token: Firebase ID token

    Returns:
        Tuple of (user_id, user_email)

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token["uid"]
        user_email = decoded_token.get("email")
        logger.info(f"✅ Token verified for user: {user_id} ({user_email})")
        return user_id, user_email
    except Exception as e:
        logger.error(f"❌ Token verification failed: {e}")
        raise HTTPException(
            status_code=401, detail="Invalid or expired ID token"
        ) from e


def _assign_tier_to_user(user_id: str, tier: str) -> RegistrationResponse:
    """
    Assign tier via Firebase Custom Claims.

    Args:
        user_id: Firebase user ID
        tier: Tier to assign (FREE, PRO, UNLIMITED)

    Returns:
        RegistrationResponse with success message

    Raises:
        HTTPException: If assignment fails
    """
    try:
        auth.set_custom_user_claims(user_id, {"tier": tier})
        logger.info(f"✅ Custom claim set: {user_id} -> {tier}")
        return RegistrationResponse(
            status="success",
            tier=tier,
            message="Access to plan assigned successfully. You may need to refresh your token.",
        )
    except Exception as e:
        logger.error(f"❌ Failed to set custom claims: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to assign tier. Please try again."
        ) from e


def _validate_invitation_code(invitation_code: str, db: Any) -> dict[str, Any]:
    """
    Validate invitation code and return code data.

    Args:
        invitation_code: Invitation code to validate
        db: Firestore database client

    Returns:
        Code data dictionary

    Raises:
        HTTPException: If code is invalid, used, or expired
    """
    code_ref = db.collection("invitation_codes").document(invitation_code)

    try:
        code_doc = code_ref.get()
    except Exception as e:
        logger.error(f"❌ Firestore error fetching code: {e}")
        raise HTTPException(
            status_code=500, detail="Database error. Please try again."
        ) from e

    if not code_doc.exists:
        logger.warning(f"❌ Invitation code not found: {invitation_code}")
        raise HTTPException(status_code=400, detail="Invalid invitation code")

    code_data = code_doc.to_dict()

    if not code_data:
        logger.error(f"❌ Code document exists but returned None: {invitation_code}")
        raise HTTPException(status_code=500, detail="Invalid code data")

    if code_data.get("is_used", True):
        logger.warning(f"❌ Invitation code already used: {invitation_code}")
        raise HTTPException(
            status_code=400, detail="Invitation code has already been used"
        )

    _check_code_expiration(invitation_code, code_data.get("expires_at"))

    return dict(code_data)  # type: ignore[no-any-return]


def _check_code_expiration(invitation_code: str, expires_at: Any) -> None:
    """
    Check if invitation code has expired.

    Args:
        invitation_code: Code being checked
        expires_at: Expiration timestamp from Firestore

    Raises:
        HTTPException: If code has expired
    """
    if not expires_at:
        return

    try:
        if hasattr(expires_at, "to_datetime"):
            expiration_date = expires_at.to_datetime()
        else:
            expiration_date = expires_at
        now = datetime.now(timezone.utc)

        if expiration_date.tzinfo is None:
            expiration_date = expiration_date.replace(tzinfo=timezone.utc)

        if now > expiration_date:
            logger.warning(
                f"❌ Invitation code expired: {invitation_code} "
                f"(expired: {expiration_date})"
            )
            raise HTTPException(status_code=400, detail="Invitation code has expired")
    except HTTPException:
        raise
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"⚠️ Error checking expiration date: {e}")


def _mark_code_as_used(code_ref: Any, user_id: str, invitation_code: str) -> None:
    """
    Mark invitation code as used in Firestore.

    Args:
        code_ref: Firestore document reference
        user_id: User who used the code
        invitation_code: Code that was used
    """
    try:
        code_ref.update(
            {"is_used": True, "used_by_user_id": user_id, "used_at": SERVER_TIMESTAMP}
        )
        logger.info(f"✅ Invitation code marked as used: {invitation_code}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"❌ Failed to mark code as used: {e}")


@router.post("/register", response_model=RegistrationResponse)
async def register_user(registration_data: RegistrationData) -> RegistrationResponse:
    """
    Register user and assign tier based on invitation code or unlimited email list.

    Flow:
    1. Verify Firebase ID token
    2. Check if user email is in unlimited list (skip invitation code if true)
    3. Validate invitation code (if not in unlimited list)
    4. Assign tier via Firebase Custom Claims
    5. Mark invitation code as used (if applicable)

    Args:
        registration_data: Registration request with ID token and optional invitation code

    Returns:
        RegistrationResponse with assigned tier

    Raises:
        HTTPException 401: Invalid or expired ID token
        HTTPException 400: Invalid, used, or expired invitation code
    """
    logger.info("🔐 Processing user registration request")

    # Step 1: Verify Firebase ID token
    user_id, user_email = _verify_token_and_get_user_info(registration_data.id_token)

    # Step 2: Check if user is in unlimited emails list
    app_config = load_app_config()
    unlimited_emails = app_config["unlimited_emails"]

    if user_email and user_email in unlimited_emails:
        logger.info(
            f"🌟 User {user_email} found in unlimited list - assigning UNLIMITED tier"
        )
        return _assign_tier_to_user(user_id, "UNLIMITED")

    # Step 3: Validate invitation code (required if not in unlimited list)
    if not registration_data.invitation_code:
        logger.warning(
            f"❌ User {user_email} not in unlimited list and no invitation code provided"
        )
        raise HTTPException(
            status_code=400, detail="Invitation code is required for registration"
        )

    invitation_code = registration_data.invitation_code.strip()
    db = get_db()

    # Step 4: Validate invitation code
    code_data = _validate_invitation_code(invitation_code, db)
    assigned_tier = code_data.get("tier", "FREE")
    logger.info(f"✅ Valid invitation code - assigning tier: {assigned_tier}")

    # Step 5: Assign tier to user
    response = _assign_tier_to_user(user_id, assigned_tier)

    # Step 6: Mark invitation code as used
    code_ref = db.collection("invitation_codes").document(invitation_code)
    _mark_code_as_used(code_ref, user_id, invitation_code)

    return response


@router.post("/refresh-claims")
def refresh_user_claims(id_token: str) -> Dict[str, Any]:
    """
    Retrieve current user claims from Firebase token.

    Useful for frontend to check current tier after registration.

    Args:
        id_token: Firebase ID token

    Returns:
        Dict with user claims including tier

    Raises:
        HTTPException 401: Invalid token
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token["uid"]

        # Get fresh claims from Firebase
        user = auth.get_user(user_id)
        claims = user.custom_claims or {}

        return {
            "status": "success",
            "tier": claims.get("tier", "FREE"),
            "claims": claims,
        }

    except Exception as e:
        logger.error(f"❌ Failed to refresh claims: {e}")
        raise HTTPException(status_code=401, detail="Invalid token") from e


@router.post("/request-invitation-code", response_model=InvitationCodeRequestResponse)
async def request_invitation_code(
    request: InvitationCodeRequest, email_service: Any = Depends(get_email_service)
) -> InvitationCodeRequestResponse:
    """
    Send invitation code request to support team.

    User provides their name and email to request an invitation code.
    Support team will receive an email with the request details.

    Args:
        request: User information (first_name, last_name, email)
        email_service: Email service dependency

    Returns:
        InvitationCodeRequestResponse with confirmation message

    Raises:
        HTTPException 500: Failed to send email
    """
    logger.info(
        f"📧 Invitation code requested | User: {request.first_name} {request.last_name} | "
        f"Email: {request.email}"
    )

    try:
        # Send email to support
        success = email_service.send_invitation_request(
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
        )

        if success:
            logger.info(
                f"✅ Invitation request email sent successfully for {request.email}"
            )
            return InvitationCodeRequestResponse(
                status="success",
                message=(
                    "Your request has been sent to our support team. "
                    "You will receive an invitation code via email soon."
                ),
            )
        else:
            logger.error(
                f"❌ Failed to send invitation request email for {request.email}"
            )
            raise HTTPException(
                status_code=500,
                detail=(
                    "Failed to send your request. "
                    "Please try again later or contact support directly."
                ),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing invitation request: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request. Please try again later.",
        ) from e


@router.get("/tier-limits")
def get_tier_limits() -> Dict[str, Any]:
    """
    Get tier limits configuration from Firestore.

    Returns limits for all tiers (FREE, PRO, UNLIMITED).
    Used by frontend to display tier information and limits.

    Returns:
        dict: Dictionary with tier limits
    """
    try:
        app_config = load_app_config()
        limits = app_config["limits"]

        logger.info("✅ Tier limits retrieved successfully")
        return {"status": "success", "limits": limits}
    except Exception as e:
        logger.error(f"❌ Error retrieving tier limits: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve tier limits"
        ) from e


@router.get("/usage")
async def get_user_usage(user_id: str = Depends(get_current_user_id)) -> Dict[str, Any]:
    """
    Get current user's query usage for today.

    Retrieves the number of queries the user has made today and compares
    it with their tier limit. Returns usage statistics and remaining quota.

    Args:
        user_id: User ID from Firebase token (injected by dependency)

    Returns:
        dict: {
            "status": "success",
            "queries_today": int,
            "query_limit": int,
            "remaining": int,
            "tier": str
        }
    """
    try:
        # Get user's tier from Firebase
        user = auth.get_user(user_id)
        custom_claims = user.custom_claims or {}
        tier = custom_claims.get("tier", "FREE")

        # Get tier limits
        app_config = load_app_config()
        tier_limits = app_config["limits"].get(tier, app_config["limits"]["FREE"])
        query_limit = tier_limits["max_queries_per_day"]

        # Get usage service and fetch today's query count
        usage_service = get_usage_service()
        queries_today = usage_service.get_user_queries_today(user_id)

        # Calculate remaining queries using helper function
        remaining = calculate_remaining_queries(query_limit, queries_today)

        logger.info(
            f"📊 Usage retrieved for user {user_id}: {queries_today}/{query_limit} ({tier})"
        )

        return {
            "status": "success",
            "queries_today": queries_today,
            "query_limit": query_limit,
            "remaining": remaining,
            "tier": tier,
        }
    except Exception as e:
        logger.error(f"❌ Error retrieving user usage: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve usage information"
        ) from e


@router.post("/admin/set-tier")
def set_user_tier_admin(
    email: str, tier: str, _current_user_id: str = Depends(get_current_user_id)
) -> Dict[str, str]:
    """
    ADMIN ENDPOINT: Set tier for a user by email.

    ⚠️ TEMPORARY ENDPOINT FOR DEVELOPMENT
    TODO: Add proper admin authentication before production

    Args:
        email: User email to update
        tier: Tier to set (FREE, PRO, or UNLIMITED)

    Returns:
        Success message with user details
    """
    try:
        # Validate tier
        valid_tiers = ["FREE", "PRO", "UNLIMITED"]
        if tier not in valid_tiers:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tier. Must be one of: {', '.join(valid_tiers)}",
            )

        # Get user by email
        user = auth.get_user_by_email(email)

        logger.info(f"🔧 Setting tier={tier} for user {email} (uid={user.uid})")

        # Set custom claim
        auth.set_custom_user_claims(user.uid, {"tier": tier})

        logger.info(f"✅ Tier set successfully for {email}")

        return {
            "message": f"Tier set to {tier} for {email}",
            "user_id": user.uid,
            "email": email,
            "tier": tier,
            "note": "User must log out and log back in for changes to take effect",
        }

    except auth.UserNotFoundError as exc:
        logger.error(f"❌ User not found: {email}")
        raise HTTPException(status_code=404, detail=f"User not found: {email}") from exc
    except Exception as e:
        logger.error(f"❌ Error setting tier: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to set tier: {str(e)}"
        ) from e
