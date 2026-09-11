"""Compatibility imports for the Resend email adapter."""

from app.infrastructure.resend_email_adapter import (
    ResendEmailAdapter,
    get_email_service,
)

EmailService = ResendEmailAdapter

__all__ = ["EmailService", "get_email_service"]
