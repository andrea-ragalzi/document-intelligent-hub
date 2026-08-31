"""Security boundaries for authenticated bug-report and feedback submissions."""

import io
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.auth import verify_firebase_token
from app.services.email_service import EmailService
from main import app


@pytest.fixture
def support_client() -> TestClient:
    """Client with a verified UID and no external email delivery."""
    app.dependency_overrides[verify_firebase_token] = lambda: "verified-user"
    from app.routers.support_router import support_rate_limiter

    support_rate_limiter.clear()
    with patch("app.routers.support_router.get_email_service") as get_email_service:
        email_service = Mock()
        email_service.send_bug_report.return_value = True
        email_service.send_feedback.return_value = True
        get_email_service.return_value = email_service
        with TestClient(app) as test_client:
            yield test_client
    app.dependency_overrides.pop(verify_firebase_token, None)
    support_rate_limiter.clear()


def _bug_data(**overrides: str) -> dict[str, str]:
    data = {"description": "The upload button did not respond."}
    data.update(overrides)
    return data


def _feedback_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {"rating": 5, "message": "Useful document answers."}
    payload.update(overrides)
    return payload


def test_bug_report_without_token_is_rejected() -> None:
    with TestClient(app) as client:
        response = client.post("/rag/report-bug/", data=_bug_data())

    assert response.status_code == 401


def test_feedback_without_token_is_rejected() -> None:
    with TestClient(app) as client:
        response = client.post("/rag/feedback/", json=_feedback_payload())

    assert response.status_code == 401


def test_bug_report_uses_verified_uid_not_client_input(support_client: TestClient) -> None:
    with patch("app.routers.support_router.get_email_service") as get_email_service:
        email_service = Mock()
        email_service.send_bug_report.return_value = True
        get_email_service.return_value = email_service

        response = support_client.post(
            "/rag/report-bug/", data=_bug_data(user_id="forged-victim")
        )

    assert response.status_code == 201
    assert email_service.send_bug_report.call_args.kwargs["user_id"] == "verified-user"


def test_foreign_conversation_is_rejected(support_client: TestClient) -> None:
    conversation = Mock()
    conversation.exists = True
    conversation.to_dict.return_value = {"userId": "another-user"}
    db = Mock()
    db.collection.return_value.document.return_value.get.return_value = conversation

    with patch("app.routers.support_router.firestore.client", return_value=db):
        response = support_client.post(
            "/rag/feedback/",
            json=_feedback_payload(conversation_id="foreign-conversation"),
        )

    assert response.status_code == 404


def test_bug_report_html_escapes_user_controlled_values() -> None:
    html = EmailService()._build_bug_report_html(
        user_id="<user>",
        description="<img src=x onerror=alert(1)>",
        conversation_id="<conversation>",
        timestamp="<time>",
        user_agent="<agent>",
        attachment_filename="<file>.png",
        attachment_type="image/png",
    )

    assert "&lt;img src=x onerror=alert(1)&gt;" in html
    assert "<img src=x onerror=alert(1)>" not in html
    assert "&lt;file&gt;.png" in html


def test_feedback_html_escapes_user_controlled_values() -> None:
    html = EmailService()._build_feedback_html(
        user_id="<user>",
        rating=5,
        message="<script>alert(1)</script>",
        conversation_id="<conversation>",
        timestamp="<time>",
        user_agent="<agent>",
        star_visual="★★★★★",
        sentiment="Positive",
        sentiment_color="#16a34a",
        emoji="😊",
    )

    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<script>alert(1)</script>" not in html


def test_unsupported_bug_attachment_is_rejected(support_client: TestClient) -> None:
    response = support_client.post(
        "/rag/report-bug/",
        data=_bug_data(),
        files={"attachment": ("payload.exe", io.BytesIO(b"not allowed"), "application/x-msdownload")},
    )

    assert response.status_code == 415


def test_bug_attachment_over_ten_mb_is_rejected(support_client: TestClient) -> None:
    response = support_client.post(
        "/rag/report-bug/",
        data=_bug_data(),
        files={"attachment": ("large.pdf", io.BytesIO(b"X" * (11 * 1024 * 1024)), "application/pdf")},
    )

    assert response.status_code == 413


def test_oversized_support_text_is_rejected(support_client: TestClient) -> None:
    response = support_client.post(
        "/rag/feedback/", json=_feedback_payload(message="x" * 2_001)
    )

    assert response.status_code == 422


def test_feedback_rejects_client_controlled_identity_fields(support_client: TestClient) -> None:
    response = support_client.post(
        "/rag/feedback/",
        json=_feedback_payload(user_id="forged-victim", timestamp="forged-time"),
    )

    assert response.status_code == 422


def test_bug_report_rate_limit_returns_429(support_client: TestClient) -> None:
    from app.routers import support_router

    support_router.support_rate_limiter.clear()
    for _ in range(5):
        assert support_client.post("/rag/report-bug/", data=_bug_data()).status_code == 201

    response = support_client.post("/rag/report-bug/", data=_bug_data())

    assert response.status_code == 429


def test_valid_authenticated_support_requests_work(support_client: TestClient) -> None:
    from app.routers import support_router

    support_router.support_rate_limiter.clear()
    bug_response = support_client.post("/rag/report-bug/", data=_bug_data())
    feedback_response = support_client.post("/rag/feedback/", json=_feedback_payload())

    assert bug_response.status_code == 201
    assert feedback_response.status_code == 201
