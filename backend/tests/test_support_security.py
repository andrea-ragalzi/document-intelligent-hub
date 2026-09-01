import io
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.auth import verify_firebase_token
from app.services.email_service import EmailService
from main import app


@pytest.fixture
def support_client() -> TestClient:
    from app.routers.support_router import support_rate_limiter

    support_rate_limiter.clear()
    app.dependency_overrides[verify_firebase_token] = lambda: "verified-user"
    with patch("app.routers.support_router.get_email_service") as factory:
        service = Mock()
        service.send_bug_report.return_value = True
        service.send_feedback.return_value = True
        factory.return_value = service
        with TestClient(app) as test_client:
            test_client.email_service = service  # type: ignore[attr-defined]
            yield test_client
    app.dependency_overrides.pop(verify_firebase_token, None)
    support_rate_limiter.clear()


def test_unauthenticated_submissions_are_rejected() -> None:
    with patch("app.routers.support_router.get_email_service") as factory:
        service = Mock()
        factory.return_value = service
        with TestClient(app) as client:
            assert client.post("/rag/report-bug/", data={"description": "A valid report."}).status_code == 401
            assert client.post("/rag/feedback/", json={"message": "Useful application."}).status_code == 401
    service.send_bug_report.assert_not_called()
    service.send_feedback.assert_not_called()


def test_forged_identity_is_not_forwarded(support_client: TestClient) -> None:
    response = support_client.post("/rag/report-bug/", data={"description": "A valid report.", "user_id": "victim"})
    assert response.status_code == 201
    assert support_client.email_service.send_bug_report.call_args.kwargs["user_id"] == "verified-user"  # type: ignore[attr-defined]
    assert len(support_client.email_service.send_bug_report.call_args.kwargs["report_id"]) == 32  # type: ignore[attr-defined]


def test_rejections_do_not_send_email(support_client: TestClient) -> None:
    service = support_client.email_service  # type: ignore[attr-defined]
    assert support_client.post("/rag/report-bug/", data={"description": "x" * 1501}).status_code == 422
    response = support_client.post("/rag/report-bug/", data={"description": "Invalid screenshot."}, files={"attachment": ("bad.png", io.BytesIO(b"bad"), "image/png")})
    assert response.status_code == 415
    assert support_client.post("/rag/feedback/", json={"message": "x" * 1001}).status_code == 422
    assert service.send_bug_report.call_count == 0
    assert service.send_feedback.call_count == 0


def test_feedback_rejects_extra_and_rapid_submissions(support_client: TestClient) -> None:
    assert support_client.post("/rag/feedback/", json={"message": "Useful application.", "user_id": "victim"}).status_code == 422
    assert support_client.post("/rag/feedback/", json={"message": "Useful application."}).status_code == 201
    response = support_client.post("/rag/feedback/", json={"message": "Repeated immediately."})
    assert response.status_code == 429
    assert response.json() == {"detail": "Too many support submissions. Please try again later."}
    support_client.email_service.send_feedback.assert_called_once()  # type: ignore[attr-defined]


def test_email_provider_failure_is_generic_to_the_client(support_client: TestClient) -> None:
    support_client.email_service.send_feedback.return_value = False  # type: ignore[attr-defined]
    response = support_client.post("/rag/feedback/", json={"message": "Useful application."})
    assert response.status_code == 503
    assert response.json() == {"detail": "Unable to submit feedback. Please try again later."}
    assert "resend" not in response.text.lower()


def test_untrusted_feedback_is_sent_as_plain_text(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setenv("RESEND_FROM_EMAIL", "reports@example.com")
    monkeypatch.setenv("REPORT_RECIPIENT_EMAIL", "team@example.com")
    service = EmailService()
    with patch("app.services.email_service.resend.Emails.send", return_value={"id": "email_123"}) as send:
        assert service.send_feedback("verified-user", "<script>alert(1)</script>")

    payload = send.call_args.args[0]
    assert "html" not in payload
    assert "<script>alert(1)</script>" in payload["text"]
