#!/usr/bin/env python3
"""
Test script for bug report endpoint with ARCHIVE attachment.
Tests the /rag/report-bug endpoint with a sample ZIP file.
"""

import io
import zipfile

import requests

# Configuration
API_URL = "http://localhost:8000/rag/report-bug"
USER_ID = "test_user_archive"
CONVERSATION_ID = "test_conversation_archive_999"

def create_test_zip():
    """Create a minimal test ZIP file in memory."""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add a text file
        zip_file.writestr('bug_report_details.txt', 
                         'This is a test bug report archive.\n\n'
                         'Contents:\n'
                         '- Error logs\n'
                         '- Screenshots\n'
                         '- Configuration files\n')
        
        # Add a fake log file
        zip_file.writestr('logs/error.log', 
                         '[2025-11-23 17:10:00] ERROR: Test error message\n'
                         '[2025-11-23 17:10:01] ERROR: Another error\n'
                         '[2025-11-23 17:10:02] WARNING: Test warning\n')
        
        # Add a fake config file
        zip_file.writestr('config/settings.json', 
                         '{\n'
                         '  "debug": true,\n'
                         '  "version": "1.0.0",\n'
                         '  "test_mode": true\n'
                         '}\n')
    
    zip_buffer.seek(0)
    zip_size = len(zip_buffer.getvalue())
    print(f"✅ Created test ZIP archive: {zip_size} bytes")
    
    return zip_buffer

def test_bug_report_with_zip():
    """Test bug report submission with ZIP archive attachment."""
    
    print("🧪 Testing bug report with ZIP ARCHIVE attachment...")
    
    # Create test ZIP
    test_zip = create_test_zip()
    
    # Prepare form data
    files = {
        'attachment': ('bug_report_archive.zip', test_zip, 'application/zip')
    }
    
    data = {
        'user_id': USER_ID,
        'conversation_id': CONVERSATION_ID,
        'description': 'This is a test bug report with an attached ZIP archive containing logs, config, and other diagnostic files.',
        'timestamp': '2025-11-23T17:12:00Z',
        'user_agent': 'Python Test Script Archive/1.0',
    }
    
    try:
        print(f"📤 Sending POST request to {API_URL}")
        print(f"   User ID: {USER_ID}")
        print(f"   Conversation ID: {CONVERSATION_ID}")
        print("   Attachment: bug_report_archive.zip (application/zip) 📦")
        
        response = requests.post(API_URL, data=data, files=files)
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.ok:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"   Message: {result.get('message')}")
            print(f"   Report ID: {result.get('report_id')}")
            print(f"   Email Sent: {result.get('email_sent')}")
            print(f"   Attachment Included: {result.get('attachment_included')}")
            
            if result.get('email_sent'):
                print("\n📧 Check your support email for the bug report with ZIP archive! 📦")
            else:
                print("\n⚠️ Email was not sent (check SendGrid configuration)")
        else:
            print("❌ FAILED!")
            error_text = response.text
            print(f"   Error: {error_text}")
            
            # Check for file size error
            if response.status_code == 413:
                print("   💡 ZIP file is too large (max 10MB)")
            
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("Bug Report API Test with ZIP Archive Attachments 📦")
    print("=" * 60)
    
    test_bug_report_with_zip()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
