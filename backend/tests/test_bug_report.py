import io
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.auth import verify_firebase_token
from main import app


@pytest.fixture
def client() -> TestClient:
    from app.routers.support_router import support_rate_limiter

    support_rate_limiter.clear()
    app.dependency_overrides[verify_firebase_token] = lambda: "bug-report-user"
    with patch("app.routers.support_router.get_email_service") as factory:
        service = Mock()
        service.send_bug_report.return_value = True
        factory.return_value = service
        with TestClient(app) as test_client:
            yield test_client
    app.dependency_overrides.pop(verify_firebase_token, None)
    support_rate_limiter.clear()


def test_bug_report_accepts_a_png_screenshot(client: TestClient) -> None:
    screenshot = io.BytesIO()
    Image.new("RGB", (1, 1)).save(screenshot, format="PNG")
    screenshot.seek(0)
    response = client.post(
        "/rag/report-bug/",
        data={"description": "The upload button did not respond."},
        files={"attachment": ("ignored.png", screenshot, "image/png")},
    )
    assert response.status_code == 201


@pytest.mark.parametrize("mime_type", ["video/mp4", "application/pdf", "application/zip"])
def test_bug_report_rejects_non_screenshot_content(client: TestClient, mime_type: str) -> None:
    response = client.post(
        "/rag/report-bug/",
        data={"description": "The attached file must be rejected."},
        files={"attachment": ("payload.bin", io.BytesIO(b"not-an-image"), mime_type)},
    )
    assert response.status_code == 415


def test_bug_report_rejects_spoofed_image_mime(client: TestClient) -> None:
    response = client.post(
        "/rag/report-bug/",
        data={"description": "The declared MIME type is not trusted."},
        files={"attachment": ("payload.png", io.BytesIO(b"not-a-png"), "image/png")},
    )
    assert response.status_code == 415
