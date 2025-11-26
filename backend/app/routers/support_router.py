"""
Support Router - User Support and Configuration Endpoints

Handles support operations:
- Bug reports with attachments
- User feedback with ratings
- Supported languages list
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from app.config.languages import SUPPORTED_LANGUAGES
from app.config.security_constants import MAX_ATTACHMENT_SIZE
from app.core.logging import logger
from app.schemas.rag_schema import (
    FeedbackRequest,
    LanguageInfo,
    LanguagesListResponse,
)
from app.services.email_service import get_email_service
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

router = APIRouter(prefix="/rag", tags=["support"])


@router.get("/languages/", response_model=LanguagesListResponse, status_code=status.HTTP_200_OK)
def get_supported_languages():
    """
    **Get list of supported languages.**

    Returns language metadata:
    - Code (ISO 639-1)
    - English name
    - Native name
    - Flag emoji
    - Translated "Sources" label

    **Cache-friendly:** Languages rarely change, safe to cache client-side.
    """
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
    
    return LanguagesListResponse(
        languages=languages,
        total_count=len(languages)
    )


@router.post("/report-bug/", status_code=status.HTTP_201_CREATED)
async def report_bug(
    user_id: str = Form(..., description="User ID who is reporting the bug"),
    description: str = Form(..., min_length=10, description="Bug description (min 10 chars)"),
    conversation_id: str = Form(None, description="Optional conversation ID"),
    timestamp: str = Form(..., description="ISO timestamp when bug was reported"),
    user_agent: str = Form(None, description="Optional browser user agent"),
    attachment: UploadFile = File(None, description="Optional file attachment (max 10MB)"),
):
    """
    **Report a bug with optional attachment.**

    Features:
    - Email notification via SendGrid
    - Supports attachments (images, videos, PDFs, archives) up to 10MB
    - Structured logging to `logs/bug_reports.log`
    - Conversation context for debugging

    **Setup:** Requires `SENDGRID_API_KEY` in `.env`
    """
    # Validate attachment size (constant: 10MB for bug reports)
    if attachment and attachment.size:
        if attachment.size > MAX_ATTACHMENT_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Attachment too large. Maximum size is 10MB, got {attachment.size / 1024 / 1024:.2f}MB"
            )
    
    # Read attachment content if provided
    attachment_data = None
    attachment_filename = None
    attachment_type = None
    
    if attachment and attachment.filename:
        attachment_content = await attachment.read()
        attachment_data = attachment_content
        attachment_filename = attachment.filename
        attachment_type = attachment.content_type
        logger.info(f"📎 Attachment received | Name: {attachment_filename} | Type: {attachment_type} | Size: {len(attachment_content)} bytes")
    
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Structured log entry
    log_entry = {
        "timestamp": timestamp,
        "user_id": user_id,
        "conversation_id": conversation_id,
        "description": description,
        "user_agent": user_agent,
        "attachment_filename": attachment_filename,
        "attachment_size": len(attachment_data) if attachment_data else 0,
        "server_timestamp": datetime.now(UTC).isoformat(),
    }
    
    # Write to dedicated bug reports log
    bug_log_path = logs_dir / "bug_reports.log"
    with open(bug_log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    # Send email notification via SendGrid
    email_service = get_email_service()
    email_sent = email_service.send_bug_report(
        user_id=user_id,
        description=description,
        conversation_id=conversation_id,
        timestamp=timestamp,
        user_agent=user_agent,
        attachment_data=attachment_data,
        attachment_filename=attachment_filename,
        attachment_type=attachment_type,
    )
    
    # Log to main logs with emoji for visibility
    attachment_info = f" | 📎 {attachment_filename}" if attachment_filename else ""
    logger.bind(BUG_REPORT=True).warning(
        f"🐞 Bug Report from {user_id} | Conv: {conversation_id or 'N/A'} | Email: {'✅' if email_sent else '❌'}{attachment_info} | {description[:100]}"
    )
    
    return {
        "message": "Bug report received successfully",
        "report_id": f"{user_id}_{datetime.now(UTC).timestamp()}",
        "status": "logged",
        "email_sent": email_sent,
        "attachment_included": attachment_filename is not None,
    }


@router.post("/feedback/", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback: FeedbackRequest,
):
    """
    **Submit user feedback with star rating.**

    Features:
    - Star rating from 0.5 to 5.0 (half-star increments)
    - Optional feedback message
    - Email notification with star visualization
    - Structured logging to `logs/feedback.log`
    - Conversation context for targeted improvements

    **Setup:** Requires `SENDGRID_API_KEY` in `.env`
    """
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Structured log entry
    log_entry = {
        "timestamp": feedback.timestamp,
        "user_id": feedback.user_id,
        "conversation_id": feedback.conversation_id,
        "rating": feedback.rating,
        "message": feedback.message,
        "user_agent": feedback.user_agent,
        "server_timestamp": datetime.now(UTC).isoformat(),
    }
    
    # Write to dedicated feedback log
    feedback_log_path = logs_dir / "feedback.log"
    with open(feedback_log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    # Send email notification via SendGrid
    email_service = get_email_service()
    email_sent = email_service.send_feedback(
        user_id=feedback.user_id,
        rating=feedback.rating,
        message=feedback.message,
        conversation_id=feedback.conversation_id,
        timestamp=feedback.timestamp,
        user_agent=feedback.user_agent,
    )
    
    # Determine sentiment emoji for logging
    if feedback.rating >= 4.0:
        sentiment_emoji = "😊"
    elif feedback.rating >= 3.0:
        sentiment_emoji = "😐"
    else:
        sentiment_emoji = "😞"
    
    # Log to main logs with emoji for visibility
    logger.bind(FEEDBACK=True).info(
        f"{sentiment_emoji} Feedback from {feedback.user_id} | Rating: {feedback.rating}/5.0 | Conv: {feedback.conversation_id or 'N/A'} | Email: {'✅' if email_sent else '❌'} | {feedback.message[:100] if feedback.message else 'No message'}"
    )
    
    return {
        "message": "Feedback received successfully",
        "feedback_id": f"{feedback.user_id}_{datetime.now(UTC).timestamp()}",
        "status": "logged",
        "email_sent": email_sent,
    }
