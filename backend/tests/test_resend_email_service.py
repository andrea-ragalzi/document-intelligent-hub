from unittest.mock import patch

from app.services.email_service import EmailService


def _configured_service(monkeypatch) -> EmailService:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("RESEND_API_KEY", "re_test_secret")
    monkeypatch.setenv("RESEND_FROM_EMAIL", "DIH <reports@example.com>")
    monkeypatch.setenv("REPORT_RECIPIENT_EMAIL", "team@example.com")
    return EmailService()


def test_bug_report_is_sent_with_fixed_sender_and_recipient(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    service = _configured_service(monkeypatch)
    with patch("app.services.email_service.resend.Emails.send", return_value={"id": "email_123"}) as send:
        assert service.send_bug_report(
            report_id="report_123",
            user_id="authenticated-user",
            description="The upload button did not respond.",
            timestamp="2026-09-01T12:00:00+00:00",
            user_agent="Test browser",
        )

    payload = send.call_args.args[0]
    assert payload["from"] == "DIH <reports@example.com>"
    assert payload["to"] == ["team@example.com"]
    assert payload["subject"] == "DIH bug report"
    assert "Report ID: report_123" in payload["text"]
    assert "re_test_secret" not in payload["text"]


def test_feedback_is_sent_with_fixed_sender_and_recipient(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    service = _configured_service(monkeypatch)
    with patch("app.services.email_service.resend.Emails.send", return_value={"id": "email_456"}) as send:
        assert service.send_feedback(
            feedback_id="feedback_456",
            user_id="authenticated-user",
            message="Useful document answers.",
            timestamp="2026-09-01T12:00:00+00:00",
            user_agent="Test browser",
        )

    payload = send.call_args.args[0]
    assert payload["from"] == "DIH <reports@example.com>"
    assert payload["to"] == ["team@example.com"]
    assert payload["subject"] == "DIH feedback"
    assert "Feedback ID: feedback_456" in payload["text"]
    assert "re_test_secret" not in payload["text"]


def test_resend_failure_is_not_raised_to_callers(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    service = _configured_service(monkeypatch)
    with patch(
        "app.services.email_service.resend.Emails.send",
        side_effect=RuntimeError("provider response with private details"),
    ):
        assert not service.send_feedback("authenticated-user", "Useful application.")
