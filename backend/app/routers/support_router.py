"""Authenticated bug-report, feedback, and language support endpoints."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status
from firebase_admin import firestore

from app.config.languages import SUPPORTED_LANGUAGES
from app.config.security_constants import (
    ALLOWED_ATTACHMENT_MIME_TYPES,
    MAX_ATTACHMENT_SIZE,
    MAX_BUG_REPORT_DESCRIPTION_LENGTH,
    MAX_SUPPORT_CONVERSATION_ID_LENGTH,
    MAX_SUPPORT_USER_AGENT_LENGTH,
)
from app.core.auth import verify_firebase_token
from app.core.logging import logger
from app.core.security import sanitize_filename, sanitize_log_value
from app.schemas.rag_schema import FeedbackRequest, LanguageInfo, LanguagesListResponse
from app.services.email_service import get_email_service
from app.services.support_rate_limiter import support_rate_limiter

router = APIRouter(prefix="/rag", tags=["support"])


def _server_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _short_user_id(user_id: str) -> str:
    return sanitize_log_value(user_id[:12])


def _verify_conversation_ownership(conversation_id: str | None, user_id: str) -> str | None:
    """Ensure an optional support reference belongs to the authenticated user."""
    if not conversation_id:
        return None
    try:
        snapshot = firestore.client().collection("conversations").document(conversation_id).get()
    except Exception as exc:
        logger.error("Support conversation lookup failed | Type: {}", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to verify conversation. Please try again.",
        ) from exc

    if not snapshot.exists or (snapshot.to_dict() or {}).get("userId") != user_id:
        logger.warning(
            "Rejected support submission with unowned conversation | UID: {}",
            _short_user_id(user_id),
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation_id


async def _reserve_support_submission(event_type: str, user_id: str) -> None:
    if not await support_rate_limiter.allow(event_type, user_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many support submissions. Please try again later.",
            headers={"Retry-After": "3600"},
        )


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
    description: str = Form(..., min_length=10, max_length=MAX_BUG_REPORT_DESCRIPTION_LENGTH),
    conversation_id: str | None = Form(None, max_length=MAX_SUPPORT_CONVERSATION_ID_LENGTH),
    attachment: UploadFile | None = File(None),
    user_agent: str | None = Header(None, alias="User-Agent"),
    user_id: str = Depends(verify_firebase_token),
) -> dict[str, Any]:
    """Submit an authenticated bug report without storing its free-form text."""
    await _reserve_support_submission("bug_report", user_id)
    conversation_id = _verify_conversation_ownership(conversation_id, user_id)

    attachment_data: bytes | None = None
    attachment_filename: str | None = None
    attachment_type: str | None = None
    if attachment:
        attachment_type = attachment.content_type or ""
        if attachment_type not in ALLOWED_ATTACHMENT_MIME_TYPES:
            raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported attachment type")
        if attachment.size and attachment.size > MAX_ATTACHMENT_SIZE:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Attachment exceeds the 10MB limit")
        attachment_data = await attachment.read(MAX_ATTACHMENT_SIZE + 1)
        if len(attachment_data) > MAX_ATTACHMENT_SIZE:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Attachment exceeds the 10MB limit")
        attachment_filename = sanitize_filename(attachment.filename or "unnamed_file")

    email_sent = get_email_service().send_bug_report(
        user_id=user_id,
        description=description,
        conversation_id=conversation_id,
        timestamp=_server_timestamp(),
        user_agent=(user_agent or "")[:MAX_SUPPORT_USER_AGENT_LENGTH] or None,
        attachment_data=attachment_data,
        attachment_filename=attachment_filename,
        attachment_type=attachment_type,
    )
    logger.bind(BUG_REPORT=True).info(
        "Bug report received | UID: {} | Conversation: {} | Attachment: {} | Email: {}",
        _short_user_id(user_id),
        sanitize_log_value(conversation_id or "N/A"),
        bool(attachment_filename),
        "sent" if email_sent else "not_sent",
    )
    return {
        "message": "Bug report received successfully",
        "report_id": f"report_{uuid4().hex}",
        "status": "accepted",
        "email_sent": email_sent,
        "attachment_included": attachment_filename is not None,
    }


@router.post("/feedback/", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback: FeedbackRequest,
    user_agent: str | None = Header(None, alias="User-Agent"),
    user_id: str = Depends(verify_firebase_token),
) -> dict[str, Any]:
    """Submit authenticated feedback without storing its free-form message."""
    await _reserve_support_submission("feedback", user_id)
    conversation_id = _verify_conversation_ownership(feedback.conversation_id, user_id)
    email_sent = get_email_service().send_feedback(
        user_id=user_id,
        rating=feedback.rating,
        message=feedback.message,
        conversation_id=conversation_id,
        timestamp=_server_timestamp(),
        user_agent=(user_agent or "")[:MAX_SUPPORT_USER_AGENT_LENGTH] or None,
    )
    logger.bind(FEEDBACK=True).info(
        "Feedback received | UID: {} | Rating: {} | Conversation: {} | Email: {}",
        _short_user_id(user_id),
        feedback.rating,
        sanitize_log_value(conversation_id or "N/A"),
        "sent" if email_sent else "not_sent",
    )
    return {
        "message": "Feedback received successfully",
        "feedback_id": f"feedback_{uuid4().hex}",
        "status": "accepted",
        "email_sent": email_sent,
    }
