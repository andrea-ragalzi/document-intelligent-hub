"""
Test suite for bug report functionality with file attachments.
Tests the /rag/report-bug endpoint with various scenarios.
"""

import io
import json
from pathlib import Path

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestBugReportEndpoint:
    """Test cases for the bug report endpoint."""

    def test_bug_report_without_attachment(self) -> None:
        """Test bug report submission without file attachment."""
        data = {
            "user_id": "test_user_123",
            "conversation_id": "test_conv_456",
            "description": "This is a test bug report without any attachment.",
            "timestamp": "2025-11-23T10:00:00Z",
            "user_agent": "pytest/1.0",
        }

        response = client.post("/rag/report-bug/", data=data)

        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["message"] == "Bug report received successfully"
        assert result["status"] == "logged"
        assert "report_id" in result
        assert result["attachment_included"] is False
        # Email sending depends on SendGrid configuration
        assert "email_sent" in result

    def test_bug_report_with_image_attachment(self) -> None:
        """Test bug report with image attachment."""
        # Create a minimal PNG image (1x1 pixel)
        png_data = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01"
            b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )

        files = {
            "attachment": ("test_screenshot.png", io.BytesIO(png_data), "image/png")
        }
        data = {
            "user_id": "test_user_image",
            "description": "Bug report with screenshot attachment",
            "timestamp": "2025-11-23T10:01:00Z",
        }

        response = client.post("/rag/report-bug/", data=data, files=files)

        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["attachment_included"] is True

    def test_bug_report_with_pdf_attachment(self) -> None:
        """Test bug report with PDF attachment."""
        # Minimal PDF file
        pdf_data = (
            b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj "
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj "
            b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
            b"xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n"
            b"0000000052 00000 n\n0000000101 00000 n\n"
            b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF"
        )

        files = {
            "attachment": ("error_report.pdf", io.BytesIO(pdf_data), "application/pdf")
        }
        data = {
            "user_id": "test_user_pdf",
            "description": "Bug report with PDF documentation",
            "timestamp": "2025-11-23T10:02:00Z",
        }

        response = client.post("/rag/report-bug/", data=data, files=files)

        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["attachment_included"] is True

    def test_bug_report_with_video_attachment(self) -> None:
        """Test bug report with video attachment (small dummy file)."""
        # Create dummy video data (not a real video, just for testing)
        video_data = b"DUMMY_VIDEO_DATA_FOR_TESTING" * 100

        files = {"attachment": ("bug_video.mp4", io.BytesIO(video_data), "video/mp4")}
        data = {
            "user_id": "test_user_video",
            "description": "Bug report with video recording of the issue",
            "timestamp": "2025-11-23T10:03:00Z",
        }

        response = client.post("/rag/report-bug/", data=data, files=files)

        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["attachment_included"] is True

    def test_bug_report_with_zip_attachment(self) -> None:
        """Test bug report with ZIP archive attachment."""
        import zipfile  # pylint: disable=import-outside-toplevel

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("logs.txt", "Error log content here")
            zip_file.writestr("config.json", '{"debug": true}')

        zip_buffer.seek(0)

        files = {"attachment": ("diagnostic_data.zip", zip_buffer, "application/zip")}
        data = {
            "user_id": "test_user_archive",
            "description": "Bug report with diagnostic archive",
            "timestamp": "2025-11-23T10:04:00Z",
        }

        response = client.post("/rag/report-bug/", data=data, files=files)

        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["attachment_included"] is True

    def test_bug_report_file_too_large(self) -> None:
        """Test that files larger than 10MB are rejected."""
        # Create a file larger than 10MB (10 * 1024 * 1024 bytes)
        large_data = b"X" * (11 * 1024 * 1024)  # 11MB

        files = {
            "attachment": (
                "large_file.bin",
                io.BytesIO(large_data),
                "application/octet-stream",
            )
        }
        data = {
            "user_id": "test_user_large",
            "description": "Attempting to upload a file that is too large",
            "timestamp": "2025-11-23T10:05:00Z",
        }

        response = client.post("/rag/report-bug/", data=data, files=files)

        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        result = response.json()
        assert "detail" in result
        assert "10MB" in result["detail"]

    def test_bug_report_description_too_short(self) -> None:
        """Test that descriptions shorter than 10 characters are rejected."""
        data = {
            "user_id": "test_user_short",
            "description": "Short",  # Only 5 characters
            "timestamp": "2025-11-23T10:06:00Z",
        }

        response = client.post("/rag/report-bug/", data=data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_bug_report_missing_required_fields(self) -> None:
        """Test that missing required fields are rejected."""
        # Missing description
        data = {
            "user_id": "test_user_missing",
            "timestamp": "2025-11-23T10:07:00Z",
        }

        response = client.post("/rag/report-bug/", data=data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_bug_report_with_all_optional_fields(self) -> None:
        """Test bug report with all optional fields provided."""
        png_data = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01"
            b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )

        files = {"attachment": ("full_report.png", io.BytesIO(png_data), "image/png")}
        data = {
            "user_id": "test_user_full",
            "conversation_id": "test_conv_full_789",
            "description": "Complete bug report with all fields and attachment",
            "timestamp": "2025-11-23T10:08:00Z",
            "user_agent": "Mozilla/5.0 (Test Browser) pytest/1.0",
        }

        response = client.post("/rag/report-bug/", data=data, files=files)

        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["attachment_included"] is True
        assert "report_id" in result
        assert "test_user_full" in result["report_id"]

    def test_bug_report_logs_written(self) -> None:
        """Test that bug reports are logged to file."""
        data = {
            "user_id": "test_user_logs",
            "description": "Testing that logs are written correctly",
            "timestamp": "2025-11-23T10:09:00Z",
        }

        response = client.post("/rag/report-bug/", data=data)

        assert response.status_code == status.HTTP_201_CREATED

        # Check that log file exists and contains the report
        log_path = Path("logs/bug_reports.log")
        assert log_path.exists()

        # Read the last line of the log file
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            last_log = json.loads(lines[-1])
            assert last_log["user_id"] == "test_user_logs"
            assert last_log["description"] == "Testing that logs are written correctly"

    def test_bug_report_multiple_file_types(self) -> None:
        """Test that various file types are accepted."""
        file_types = [
            ("test.png", b"PNG_DATA", "image/png"),
            ("test.jpg", b"JPEG_DATA", "image/jpeg"),
            ("test.gif", b"GIF_DATA", "image/gif"),
            ("test.pdf", b"PDF_DATA", "application/pdf"),
            ("test.mp4", b"VIDEO_DATA", "video/mp4"),
            ("test.webm", b"VIDEO_DATA", "video/webm"),
            ("test.zip", b"ZIP_DATA", "application/zip"),
            ("test.rar", b"RAR_DATA", "application/x-rar-compressed"),
        ]

        for filename, file_data, mime_type in file_types:
            files = {"attachment": (filename, io.BytesIO(file_data), mime_type)}
            data = {
                "user_id": f"test_user_{filename.split('.')[1]}",
                "description": f"Testing {mime_type} file type support",
                "timestamp": "2025-11-23T10:10:00Z",
            }

            response = client.post("/rag/report-bug/", data=data, files=files)

            assert (
                response.status_code == status.HTTP_201_CREATED
            ), f"Failed for {mime_type}"
            result = response.json()
            assert result["attachment_included"] is True

    def test_bug_report_at_size_limit(self) -> None:
        """Test file exactly at the 10MB limit."""
        # Create file exactly 10MB
        data_10mb = b"X" * (10 * 1024 * 1024)

        files = {
            "attachment": (
                "max_size.bin",
                io.BytesIO(data_10mb),
                "application/octet-stream",
            )
        }
        data = {
            "user_id": "test_user_max_size",
            "description": "Testing file at exact 10MB limit",
            "timestamp": "2025-11-23T10:11:00Z",
        }

        response = client.post("/rag/report-bug/", data=data, files=files)

        # Should succeed - exactly at limit
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["attachment_included"] is True

    def test_bug_report_special_characters_in_description(self) -> None:
        """Test bug report with special characters in description."""
        data = {
            "user_id": "test_user_special",
            "description": "Bug with special chars: 你好 🐛 <script>alert('test')</script> & © ® ™",
            "timestamp": "2025-11-23T10:12:00Z",
        }

        response = client.post("/rag/report-bug/", data=data)

        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["status"] == "logged"


@pytest.mark.asyncio
class TestBugReportEmailService:
    """Test cases for email service (requires SendGrid config)."""

    def test_email_service_initialization(self) -> None:
        """Test that email service initializes correctly."""
        from app.services.email_service import (
            get_email_service,
        )  # pylint: disable=import-outside-toplevel

        email_service = get_email_service()
        assert email_service is not None

    def test_email_service_singleton(self) -> None:
        """Test that email service is a singleton."""
        from app.services.email_service import (
            get_email_service,
        )  # pylint: disable=import-outside-toplevel

        service1 = get_email_service()
        service2 = get_email_service()
        assert service1 is service2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
