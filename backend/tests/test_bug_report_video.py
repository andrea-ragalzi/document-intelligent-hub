#!/usr/bin/env python3
# pylint: disable=no-member  # cv2 attributes are dynamically loaded
"""
Test script for bug report endpoint with VIDEO attachment.
Tests the /rag/report-bug endpoint with a sample video file.
"""

import io
from io import BytesIO

import numpy as np
import requests

# Configuration
API_URL = "http://localhost:8000/rag/report-bug"
USER_ID = "test_user_video"
CONVERSATION_ID = "test_conversation_video_789"


def create_test_video() -> BytesIO:
    """
    Create a minimal test video using OpenCV.
    Falls back to a dummy binary if OpenCV is not available.
    """
    try:
        import cv2  # pylint: disable=import-outside-toplevel

        # Create a 2-second video at 10 fps (20 frames)
        fps = 10
        duration = 2
        frames = fps * duration
        width, height = 320, 240

        # Video writer setup
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore[attr-defined]
        video_bytes = io.BytesIO()

        # Create temporary file path
        import tempfile  # pylint: disable=import-outside-toplevel

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = tmp.name

        out = cv2.VideoWriter(tmp_path, fourcc, fps, (width, height))

        # Generate frames with changing colors
        for i in range(frames):
            # Create a frame with gradient color
            color = int(255 * (i / frames))
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            frame[:, :] = [color, 128, 255 - color]

            # Add text
            cv2.putText(
                frame,
                f"Frame {i+1}/{frames}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )
            cv2.putText(
                frame,
                "TEST BUG VIDEO",
                (50, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 0),
                2,
            )

            out.write(frame)

        out.release()

        # Read the generated video
        with open(tmp_path, "rb") as f:
            video_data = f.read()

        # Clean up
        import os  # pylint: disable=import-outside-toplevel

        os.unlink(tmp_path)

        video_bytes.write(video_data)
        video_bytes.seek(0)

        print(f"✅ Created test video: {len(video_data)} bytes")
        return video_bytes

    except ImportError:
        print("⚠️ OpenCV not available, creating dummy video file")
        # Create a minimal dummy file
        dummy_data = b"DUMMY_VIDEO_DATA_FOR_TESTING" * 100
        video_bytes = io.BytesIO(dummy_data)
        return video_bytes


def test_bug_report_with_video() -> None:
    """Test bug report submission with video attachment."""

    print("🧪 Testing bug report with VIDEO attachment...")

    # Create test video
    test_video = create_test_video()

    # Prepare form data
    files = {"attachment": ("test_bug_video.mp4", test_video, "video/mp4")}

    data = {
        "user_id": USER_ID,
        "conversation_id": CONVERSATION_ID,
        "description": "This is a test bug report with an attached VIDEO file. Testing video upload functionality.",
        "timestamp": "2025-11-23T17:05:00Z",
        "user_agent": "Python Test Script Video/1.0",
    }

    try:
        print(f"📤 Sending POST request to {API_URL}")
        print(f"   User ID: {USER_ID}")
        print(f"   Conversation ID: {CONVERSATION_ID}")
        print("   Attachment: test_bug_video.mp4 (video/mp4) 🎥")

        response = requests.post(API_URL, data=data, files=files, timeout=30)

        print(f"\n📥 Response Status: {response.status_code}")

        if response.ok:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"   Message: {result.get('message')}")
            print(f"   Report ID: {result.get('report_id')}")
            print(f"   Email Sent: {result.get('email_sent')}")
            print(f"   Attachment Included: {result.get('attachment_included')}")

            if result.get("email_sent"):
                print(
                    "\n📧 Check your support email for the bug report with VIDEO attachment! 🎥"
                )
            else:
                print("\n⚠️ Email was not sent (check SendGrid configuration)")
        else:
            print("❌ FAILED!")
            error_text = response.text
            print(f"   Error: {error_text}")

            # Check for file size error
            if response.status_code == 413:
                print("   💡 Video file is too large (max 10MB)")

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Exception occurred: {str(e)}")
        import traceback  # pylint: disable=import-outside-toplevel

        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("Bug Report API Test with VIDEO Attachments 🎥")
    print("=" * 60)

    test_bug_report_with_video()

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
