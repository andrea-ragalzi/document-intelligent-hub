"""Safety checks ensuring automated tests never reach the email provider."""

from app.services.email_service import get_email_service
from main import app


def test_test_suite_overrides_the_original_email_dependency() -> None:
    """FastAPI must use the test double even for module-level TestClients."""
    assert get_email_service in app.dependency_overrides
