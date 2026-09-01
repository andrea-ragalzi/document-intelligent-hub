"""Transactional email delivery for Document Intelligent Hub.

Routes validate and authorize submissions before calling this service. It owns
the fixed Resend sender/recipient configuration and contains provider errors.
"""

import base64
import os
from typing import Optional

import resend

from app.core.logging import logger


def _safe_text(value: str | None) -> str:
    """Return plain-text field content without header-control characters."""
    return (value or "N/A").replace("\r", "").replace("\x00", "")


class EmailService:
    """Send fixed-destination transactional notifications through Resend."""

    def __init__(self) -> None:
        self.api_key = os.getenv("RESEND_API_KEY")
        self.from_email = os.getenv("RESEND_FROM_EMAIL")
        self.recipient_email = os.getenv("REPORT_RECIPIENT_EMAIL")

        if not all((self.api_key, self.from_email, self.recipient_email)):
            logger.warning("Resend email delivery is not fully configured.")
        else:
            # The official SDK reads the key from its backend-only module state.
            resend.api_key = self.api_key
            logger.info("Resend email delivery initialized.")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.from_email and self.recipient_email)

    def _send(self, payload: resend.Emails.SendParams, email_type: str) -> bool:
        """Send one message and contain provider errors inside the backend."""
        if not self.is_configured:
            logger.warning("{} email was not sent because Resend is not configured.", email_type)
            return False

        try:
            response = resend.Emails.send(payload)
        except Exception as exc:
            logger.error("{} email delivery failed | Type: {}", email_type, type(exc).__name__)
            return False

        if response.get("id"):
            logger.bind(EMAIL=True).info("{} email sent.", email_type)
            return True

        logger.error("{} email delivery failed without a provider message id.", email_type)
        return False

    def send_bug_report(
        self,
        user_id: str,
        description: str,
        conversation_id: str | None = None,
        timestamp: str | None = None,
        user_agent: str | None = None,
        attachment_data: bytes | None = None,
        attachment_filename: str | None = None,
        attachment_type: str | None = None,
        report_id: str | None = None,
    ) -> bool:
        """Send an authorized, validated bug report with an optional screenshot."""
        del conversation_id, attachment_type  # Not collected by the current safe flow.
        text = "\n".join(
            (
                "DIH bug report",
                f"Report ID: {_safe_text(report_id)}",
                f"User UID: {_safe_text(user_id)}",
                f"Timestamp: {_safe_text(timestamp)}",
                f"User agent: {_safe_text(user_agent)}",
                "",
                "Description:",
                _safe_text(description),
            )
        )
        payload: resend.Emails.SendParams = {
            "from": self.from_email or "",
            "to": [self.recipient_email or ""],
            "subject": "DIH bug report",
            "text": text,
        }
        if attachment_data and attachment_filename:
            payload["attachments"] = [
                {
                    "content": base64.b64encode(attachment_data).decode("ascii"),
                    "filename": attachment_filename,
                }
            ]
        return self._send(payload, "Bug report")

    def send_feedback(
        self,
        user_id: str,
        message: str,
        timestamp: str | None = None,
        user_agent: str | None = None,
        feedback_id: str | None = None,
    ) -> bool:
        """Send authorized plain-text feedback with fixed delivery parameters."""
        text = "\n".join(
            (
                "DIH feedback",
                f"Feedback ID: {_safe_text(feedback_id)}",
                f"User UID: {_safe_text(user_id)}",
                f"Timestamp: {_safe_text(timestamp)}",
                f"User agent: {_safe_text(user_agent)}",
                "",
                "Feedback:",
                _safe_text(message),
            )
        )
        payload: resend.Emails.SendParams = {
            "from": self.from_email or "",
            "to": [self.recipient_email or ""],
            "subject": "DIH feedback",
            "text": text,
        }
        return self._send(payload, "Feedback")

    def send_invitation_request(self, first_name: str, last_name: str, email: str) -> bool:
        """Keep the existing invitation notification on the same backend provider."""
        text = "\n".join(
            (
                "DIH invitation code request",
                f"Name: {_safe_text(first_name)} {_safe_text(last_name)}",
                f"Email: {_safe_text(email)}",
            )
        )
        payload: resend.Emails.SendParams = {
            "from": self.from_email or "",
            "to": [self.recipient_email or ""],
            "subject": "DIH invitation code request",
            "text": text,
        }
        return self._send(payload, "Invitation request")


_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create the backend email-service singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
