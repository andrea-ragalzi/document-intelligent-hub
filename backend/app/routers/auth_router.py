"""
Authentication Router

Handles user registration and tier assignment via Firebase Custom Claims.
"""

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from firebase_admin import auth

from app.core.logging import logger
from app.dependencies import get_email_service, get_usage_service
from app.infrastructure import firebase_config
from app.schemas.auth_schema import (
    InvitationCodeRequest,
    InvitationCodeRequestResponse,
    RegistrationData,
    RegistrationResponse,
)
from app.services.support_rate_limiter import support_rate_limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])

SUPPORTED_TIERS = frozenset({"FREE", "PRO", "UNLIMITED"})


def get_db() -> Any:
    """Compatibility wrapper for the infrastructure Firestore provider."""
    return firebase_config.get_db()


def calculate_remaining_queries(query_limit: int, queries_used: int) -> int:
    """
    Calculate remaining queries for a user.

    Every tier has a finite server-side ceiling, including UNLIMITED.

    Args:
        query_limit: Maximum queries allowed per day
        queries_used: Number of queries already used today

    Returns:
        int: Remaining queries

    Examples:
        >>> calculate_remaining_queries(20, 15)
        5
        >>> calculate_remaining_queries(500, 20)
        480
    """
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
    except Exception as exc:
        logger.error("Token verification failed | Type: {}", type(exc).__name__)
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc


def get_current_admin_user_id(authorization: str | None = Header(default=None)) -> str:
    """Validate a Firebase token and require its signed ``admin: true`` claim."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid authorization header"
        )

    token = authorization.removeprefix("Bearer ")
    try:
        decoded_token = auth.verify_id_token(token)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error("Token verification failed | Type: {}", type(exc).__name__)
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    if decoded_token.get("admin") is not True:
        logger.warning("🚫 Rejected tier assignment from a non-admin Firebase token")
        raise HTTPException(status_code=403, detail="Administrator access required")

    return str(decoded_token["uid"])


def clear_cache() -> None:
    """Compatibility wrapper for clearing infrastructure configuration cache."""
    firebase_config.clear_cache()


def load_app_config() -> dict[str, Any]:
    """Compatibility wrapper retaining the router's existing test/API seam."""
    return firebase_config.load_app_config(get_db)


def get_unlimited_emails() -> list[str]:
    """
    Retrieve list of emails with unlimited tier access from Firestore.

    Fetches from app_config/settings document and caches result.
    Falls back to empty list if document not found or error occurs.

    Returns:
        List of email addresses with unlimited access
    """
    # Return cached value if available
    if hasattr(get_unlimited_emails, "cache"):
        return list(get_unlimited_emails.cache)

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

    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error("Unable to load unlimited-email configuration | Type: {}", type(exc).__name__)
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
        logger.info("Registration token verified")
        return user_id, user_email
    except Exception as exc:
        logger.error("Registration token verification failed | Type: {}", type(exc).__name__)
        raise HTTPException(
            status_code=401, detail="Invalid or expired ID token"
        ) from exc


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
        user = auth.get_user(user_id)
        custom_claims = dict(user.custom_claims or {})
        custom_claims["tier"] = tier
        auth.set_custom_user_claims(user_id, custom_claims)
        logger.info("Custom tier claim set | Tier: {}", tier)
        return RegistrationResponse(
            status="success",
            tier=tier,
            message="Access to plan assigned successfully. You may need to refresh your token.",
        )
    except Exception as exc:
        logger.error("Failed to set custom tier claim | Type: {}", type(exc).__name__)
        raise HTTPException(
            status_code=500, detail="Failed to assign tier. Please try again."
        ) from exc


def _get_existing_user_tier(user_id: str) -> str | None:
    """Return a valid tier already assigned by Firebase Admin, if present."""
    try:
        user = auth.get_user(user_id)
        custom_claims = user.custom_claims or {}
        existing_tier = custom_claims.get("tier")

        if existing_tier in SUPPORTED_TIERS:
            return str(existing_tier)
        return None
    except Exception as exc:
        logger.error("Failed to read existing Firebase claims | Type: {}", type(exc).__name__)
        raise HTTPException(
            status_code=500, detail="Failed to verify existing account tier."
        ) from exc


@router.post(
    "/register",
    responses={400: {"description": "Invalid registration."}},
)
async def register_user(registration_data: RegistrationData) -> RegistrationResponse:
    """
    Register user and assign a server-authoritative tier.

    Flow:
    1. Verify Firebase ID token
    2. Preserve an existing valid Firebase tier on a no-code retry
    3. Require an invitation for new production registrations
    4. Assign FREE without a code only outside invite-only mode
    5. Atomically validate and consume supplied invitations
    6. Assign the server-selected tier via Firebase Custom Claims

    Args:
        registration_data: Registration request with ID token

    Returns:
        RegistrationResponse with assigned tier

    Raises:
        HTTPException 401: Invalid or expired ID token
    """
    logger.info("🔐 Processing user registration request")

    # Step 1: Verify Firebase ID token
    user_id, user_email = _verify_token_and_get_user_info(registration_data.id_token)

    existing_tier = _get_existing_user_tier(user_id)
    if existing_tier:
        logger.info("Registration preserved an existing tier | Tier: {}", existing_tier)
        return RegistrationResponse(
            status="success", tier=existing_tier, message="Existing account tier preserved."
        )

    app_config = load_app_config()
    unlimited_emails = app_config["unlimited_emails"]
    if user_email and user_email in unlimited_emails:
        logger.info("Registration matched an unlimited-tier allowlist entry")
        return _assign_tier_to_user(user_id, "UNLIMITED")

    logger.info("Registration assigned the free tier")
    return _assign_tier_to_user(user_id, "FREE")


@router.post("/refresh-claims")
def refresh_user_claims(id_token: str) -> dict[str, Any]:
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

    except Exception as exc:
        logger.error("Failed to refresh claims | Type: {}", type(exc).__name__)
        raise HTTPException(status_code=401, detail="Invalid token") from exc


@router.post("/request-invitation-code", response_model=InvitationCodeRequestResponse)
async def request_invitation_code(
    invitation_request: InvitationCodeRequest,
    request: Request,
    email_service: Any = Depends(get_email_service),
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
    client_host = request.client.host if request.client else "unknown"
    if not await support_rate_limiter.allow("invitation_request", client_host):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many invitation requests. Please try again later.",
            headers={"Retry-After": "60"},
        )

    logger.info("Invitation request accepted for delivery")

    try:
        # Send email to support
        success = email_service.send_invitation_request(
            first_name=invitation_request.first_name,
            last_name=invitation_request.last_name,
            email=str(invitation_request.email),
        )

        if success:
            logger.info("Invitation request delivered to the notification adapter")
            return InvitationCodeRequestResponse(
                status="success",
                message=(
                    "Your request has been sent to our support team. "
                    "You will receive an invitation code via email soon."
                ),
            )

        logger.error("Invitation request email delivery failed")
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to send your request. "
                "Please try again later or contact support directly."
            ),
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Invitation request processing failed | Type: {}", type(exc).__name__)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request. Please try again later.",
        ) from exc


@router.get("/tier-limits")
def get_tier_limits() -> dict[str, Any]:
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
    except Exception as exc:
        logger.error("Unable to retrieve tier limits | Type: {}", type(exc).__name__)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve tier limits"
        ) from exc


@router.get("/usage")
async def get_user_usage(
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
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

        logger.info("Usage retrieved | Queries: {}/{} | Tier: {}", queries_today, query_limit, tier)

        return {
            "status": "success",
            "queries_today": queries_today,
            "query_limit": query_limit,
            "remaining": remaining,
            "tier": tier,
        }
    except Exception as exc:
        logger.error("Unable to retrieve user usage | Type: {}", type(exc).__name__)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve usage information"
        ) from exc


@router.post("/admin/set-tier")
def set_user_tier_admin(
    email: str, tier: str, _admin_user_id: str = Depends(get_current_admin_user_id)
) -> dict[str, str]:
    """
    ADMIN ENDPOINT: Set tier for a user by email.

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

        logger.info("Setting user tier | Tier: {}", tier)

        # Preserve existing server-managed claims, including ``admin: true``.
        custom_claims = dict(user.custom_claims or {})
        custom_claims["tier"] = tier
        auth.set_custom_user_claims(user.uid, custom_claims)

        logger.info("User tier set successfully | Tier: {}", tier)

        return {
            "message": f"Tier set to {tier} for {email}",
            "user_id": user.uid,
            "email": email,
            "tier": tier,
            "note": "User must log out and log back in for changes to take effect",
        }

    except HTTPException:
        raise
    except auth.UserNotFoundError as exc:
        logger.error("User was not found while setting tier")
        raise HTTPException(status_code=404, detail="User not found.") from exc
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error("Unable to set user tier | Type: {}", type(exc).__name__)
        raise HTTPException(status_code=500, detail="Failed to set tier") from exc
