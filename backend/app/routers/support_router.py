"""Authenticated bug-report, feedback, and language support endpoints."""

from datetime import UTC, datetime
from io import BytesIO
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.config.languages import SUPPORTED_LANGUAGES
from app.config.security_constants import (
    MAX_BUG_REPORT_DESCRIPTION_LENGTH,
    MAX_BUG_REPORT_SCREENSHOT_SIZE,
    MAX_FEEDBACK_MESSAGE_LENGTH,
    MAX_SUPPORT_USER_AGENT_LENGTH,
)
from app.core.auth import verify_firebase_token
from app.core.logging import logger
from app.core.security import sanitize_log_value
from app.schemas.rag_schema import FeedbackRequest, LanguageInfo, LanguagesListResponse
from app.services.email_service import get_email_service
from app.services.support_rate_limiter import support_rate_limiter

router = APIRouter(prefix="/rag", tags=["support"])


def _server_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _short_user_id(user_id: str) -> str:
    return sanitize_log_value(user_id[:12])


async def _reserve_support_submission(event_type: str, user_id: str) -> None:
    if not await support_rate_limiter.allow(event_type, user_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many support submissions. Please try again later.",
            headers={"Retry-After": "3600"},
        )


def _detect_screenshot_type(data: bytes) -> tuple[str, str] | None:
    try:
        image = Image.open(BytesIO(data))
        image.verify()
    except (UnidentifiedImageError, OSError):
        return None
    formats = {"PNG": ("image/png", "png"), "JPEG": ("image/jpeg", "jpg"), "WEBP": ("image/webp", "webp")}
    return formats.get(image.format or "")


async def _read_validated_screenshot(attachment: UploadFile) -> tuple[bytes, str, str]:
    data = await attachment.read(MAX_BUG_REPORT_SCREENSHOT_SIZE + 1)
    if len(data) > MAX_BUG_REPORT_SCREENSHOT_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Screenshot exceeds the 5MB limit.",
        )
    detected_type = _detect_screenshot_type(data)
    if not detected_type:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PNG, JPEG, and WebP screenshots are supported.",
        )
    mime_type, extension = detected_type
    return data, mime_type, f"screenshot-{uuid4().hex}.{extension}"


@router.get("/languages/", response_model=LanguagesListResponse, status_code=status.HTTP_200_OK)
def get_supported_languages() -> LanguagesListResponse:
    languages = [
        LanguageInfo(
            code=lang["code"],
            english_name=lang["english_name"],
            native_name=lang["native_name"],
            flag=lang["flag"],
            sources_label=lang["sources_label"],
        )
        for lang in SUPPORTED_LANGUAGES
    ]
    return LanguagesListResponse(languages=languages, total_count=len(languages))


@router.post("/report-bug/", status_code=status.HTTP_201_CREATED)
async def report_bug(
    description: str = Form(..., min_length=1, max_length=MAX_BUG_REPORT_DESCRIPTION_LENGTH),
    attachment: UploadFile | None = File(None),
    user_agent: str | None = Header(None, alias="User-Agent"),
    user_id: str = Depends(verify_firebase_token),
) -> dict[str, Any]:
    """Submit a short authenticated bug report and an optional validated screenshot."""
    description = description.strip()
    if not description:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Description is required.")

    attachment_data: bytes | None = None
    attachment_filename: str | None = None
    attachment_type: str | None = None
    if attachment:
        attachment_data, attachment_type, attachment_filename = await _read_validated_screenshot(attachment)

    await _reserve_support_submission("bug_report", user_id)
    report_id = uuid4().hex

    email_sent = get_email_service().send_bug_report(
        report_id=report_id,
        user_id=user_id,
        description=description,
        timestamp=_server_timestamp(),
        user_agent=(user_agent or "")[:MAX_SUPPORT_USER_AGENT_LENGTH] or None,
        attachment_data=attachment_data,
        attachment_filename=attachment_filename,
        attachment_type=attachment_type,
    )
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to submit the report. Please try again later.",
        )
    logger.bind(BUG_REPORT=True).info(
        "Bug report received | UID: {} | Screenshot: {} | Email: {}",
        _short_user_id(user_id),
        bool(attachment_filename),
        "sent" if email_sent else "not_sent",
    )
    return {
        "message": "Bug report received successfully",
        "status": "accepted",
    }


@router.post("/feedback/", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback: FeedbackRequest,
    user_agent: str | None = Header(None, alias="User-Agent"),
    user_id: str = Depends(verify_firebase_token),
) -> dict[str, Any]:
    """Submit short plain-text feedback from the authenticated user."""
    message = feedback.message.strip()
    if not message:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Feedback is required.")
    if len(message) > MAX_FEEDBACK_MESSAGE_LENGTH:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Feedback is too long.")
    await _reserve_support_submission("feedback", user_id)
    feedback_id = uuid4().hex
    email_sent = get_email_service().send_feedback(
        feedback_id=feedback_id,
        user_id=user_id,
        message=message,
        timestamp=_server_timestamp(),
        user_agent=(user_agent or "")[:MAX_SUPPORT_USER_AGENT_LENGTH] or None,
    )
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to submit feedback. Please try again later.",
        )
    logger.bind(FEEDBACK=True).info(
        "Feedback received | UID: {} | Email: {}",
        _short_user_id(user_id),
        "sent" if email_sent else "not_sent",
    )
    return {
        "message": "Feedback received successfully",
        "status": "accepted",
    }
