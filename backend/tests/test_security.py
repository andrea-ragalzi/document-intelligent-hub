"""Tests for security-focused input sanitization helpers."""

from app.core.security import sanitize_log_value


def test_sanitize_log_value_escapes_line_separators() -> None:
    """Untrusted values must not be able to create additional log records."""
    assert sanitize_log_value("first\r\nsecond") == r"first\r\nsecond"
