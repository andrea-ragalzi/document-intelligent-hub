"""Firebase Auth Emulator lifecycle tests; never run against a real Firebase project."""

import os
import uuid
from collections.abc import Generator
from urllib.parse import urlparse

import pytest
from firebase_admin import auth

pytestmark = pytest.mark.firebase_emulator

EMULATOR_PROJECT_ID = "demo-dih-auth"


def _emulator_base_url() -> str:
    host = os.getenv("FIREBASE_AUTH_EMULATOR_HOST")
    project_id = os.getenv("FIREBASE_TEST_PROJECT_ID")
    if not host:
        raise RuntimeError(
            "FIREBASE_AUTH_EMULATOR_HOST is required; refusing to run Auth CRUD tests."
        )
    if project_id != EMULATOR_PROJECT_ID:
        raise RuntimeError("Firebase Auth Emulator tests require the dedicated demo-dih-auth project.")

    parsed = urlparse(f"//{host}")
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise RuntimeError("Firebase Auth Emulator tests require a loopback-only emulator host.")
    return f"http://{host}"


@pytest.fixture(scope="module", autouse=True)
def auth_emulator_url() -> str:
    return _emulator_base_url()


@pytest.fixture
def emulator_user() -> Generator[tuple[str, str, str], None, None]:
    suffix = uuid.uuid4().hex
    email = f"auth-emulator-{suffix}@example.test"
    password = "VerificationPass123!"
    user = auth.create_user(email=email, password=password, display_name="Initial name")
    try:
        yield user.uid, email, password
    finally:
        try:
            auth.delete_user(user.uid)
        except auth.UserNotFoundError:
            pass


def test_email_password_user_lifecycle_and_verification(
    emulator_user: tuple[str, str, str]
) -> None:
    """Create, read, update, verify and delete a user entirely within the emulator."""
    uid, email, _password = emulator_user

    created = auth.get_user(uid)
    assert created.email == email
    assert created.email_verified is False

    updated = auth.update_user(uid, display_name="Updated name")
    assert updated.display_name == "Updated name"
    assert auth.get_user(uid).display_name == "Updated name"

    auth.update_user(uid, email_verified=True)
    assert auth.get_user(uid).email_verified is True

    auth.delete_user(uid)
    with pytest.raises(auth.UserNotFoundError):
        auth.get_user(uid)
