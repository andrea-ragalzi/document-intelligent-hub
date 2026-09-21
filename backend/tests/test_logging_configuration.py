"""Regression coverage for test-log isolation."""

from app.core.logging import PERSISTENT_FILE_LOGGING_ENABLED


def test_pytest_does_not_write_persistent_application_logs() -> None:
    """Expected test failures must not pollute development log files."""
    assert PERSISTENT_FILE_LOGGING_ENABLED is False
