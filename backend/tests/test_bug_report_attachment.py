#!/usr/bin/env python3
"""
Test script for bug report endpoint with file attachment.
Tests the /rag/report-bug endpoint with a sample image.
"""

import io

import requests
from PIL import Image

# Configuration
API_URL = "http://localhost:8000/rag/report-bug"
USER_ID = "test_user_123"
CONVERSATION_ID = "test_conversation_456"


def create_test_image():
    """Create a simple test image in memory."""
    # Create a 400x300 red rectangle
    img = Image.new("RGB", (400, 300), color="red")

    # Add some text using draw (optional)
    from PIL import ImageDraw, ImageFont

    draw = ImageDraw.Draw(img)
    try:
        # Try to use a default font
        font = ImageFont.load_default()
    except (OSError, ImportError):
        font = None

    draw.text((150, 140), "TEST BUG SCREENSHOT", fill="white", font=font)

    # Save to BytesIO
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    return img_bytes


def test_bug_report_with_attachment():
    """Test bug report submission with file attachment."""

    print("🧪 Testing bug report with attachment...")

    # Create test image
    test_image = create_test_image()

    # Prepare form data
    files = {"attachment": ("test_screenshot.png", test_image, "image/png")}

    data = {
        "user_id": USER_ID,
        "conversation_id": CONVERSATION_ID,
        "description": "This is a test bug report with an attached screenshot. Testing the multipart form upload functionality.",
        "timestamp": "2025-11-23T16:45:00Z",
        "user_agent": "Python Test Script/1.0",
    }

    try:
        print(f"📤 Sending POST request to {API_URL}")
        print(f"   User ID: {USER_ID}")
        print(f"   Conversation ID: {CONVERSATION_ID}")
        print("   Attachment: test_screenshot.png (PNG image)")

        response = requests.post(API_URL, data=data, files=files)

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
                    "\n📧 Check your support email for the bug report with attachment!"
                )
            else:
                print("\n⚠️ Email was not sent (check SendGrid configuration)")
        else:
            print("❌ FAILED!")
            print(f"   Error: {response.text}")

    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")


def test_bug_report_without_attachment():
    """Test bug report submission without file attachment."""

    print("\n\n🧪 Testing bug report WITHOUT attachment...")

    data = {
        "user_id": USER_ID,
        "conversation_id": CONVERSATION_ID,
        "description": "This is a test bug report WITHOUT any attachment. Just plain text.",
        "timestamp": "2025-11-23T16:46:00Z",
        "user_agent": "Python Test Script/1.0",
    }

    try:
        print(f"📤 Sending POST request to {API_URL}")
        print(f"   User ID: {USER_ID}")
        print("   No attachment")

        response = requests.post(API_URL, data=data)

        print(f"\n📥 Response Status: {response.status_code}")

        if response.ok:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"   Message: {result.get('message')}")
            print(f"   Report ID: {result.get('report_id')}")
            print(f"   Email Sent: {result.get('email_sent')}")
            print(f"   Attachment Included: {result.get('attachment_included')}")
        else:
            print("❌ FAILED!")
            print(f"   Error: {response.text}")

    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")


if __name__ == "__main__":
    print("=" * 60)
    print("Bug Report API Test with File Attachments")
    print("=" * 60)

    # Test with attachment
    test_bug_report_with_attachment()

    # Test without attachment
    test_bug_report_without_attachment()

    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)
