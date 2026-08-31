"""Regression tests for the authenticated bug-report endpoint."""

import io
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.config.security_constants import ALLOWED_ATTACHMENT_MIME_TYPES
from app.core.auth import verify_firebase_token
from main import app


@pytest.fixture
def client() -> TestClient:
    from app.routers.support_router import support_rate_limiter

    support_rate_limiter.clear()
    app.dependency_overrides[verify_firebase_token] = lambda: "bug-report-user"
    with patch("app.routers.support_router.get_email_service") as get_email_service:
        email_service = Mock()
        email_service.send_bug_report.return_value = True
        get_email_service.return_value = email_service
        with TestClient(app) as test_client:
            yield test_client
    app.dependency_overrides.pop(verify_firebase_token, None)
    support_rate_limiter.clear()


def test_bug_report_accepts_authenticated_report(client: TestClient) -> None:
    response = client.post(
        "/rag/report-bug/",
        data={"description": "The upload button did not respond."},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "accepted"


@pytest.mark.parametrize("mime_type", ALLOWED_ATTACHMENT_MIME_TYPES)
def test_bug_report_accepts_only_allowlisted_attachment_types(
    client: TestClient, mime_type: str
) -> None:
    response = client.post(
        "/rag/report-bug/",
        data={"description": f"Testing supported {mime_type} attachment."},
        files={"attachment": ("report.bin", io.BytesIO(b"content"), mime_type)},
    )

    assert response.status_code == 201


def test_bug_report_sanitizes_attachment_filename(client: TestClient) -> None:
    with patch("app.routers.support_router.get_email_service") as get_email_service:
        email_service = Mock()
        email_service.send_bug_report.return_value = True
        get_email_service.return_value = email_service
        response = client.post(
            "/rag/report-bug/",
            data={"description": "The attached screenshot shows the error."},
            files={"attachment": ("../../<report>.png", io.BytesIO(b"png"), "image/png")},
        )

    assert response.status_code == 201
    assert email_service.send_bug_report.call_args.kwargs["attachment_filename"] == "report.png"


def test_bug_report_rejects_unsupported_attachment(client: TestClient) -> None:
    response = client.post(
        "/rag/report-bug/",
        data={"description": "The attached file should be rejected."},
        files={"attachment": ("payload.exe", io.BytesIO(b"binary"), "application/x-msdownload")},
    )

    assert response.status_code == 415
