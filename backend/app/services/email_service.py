"""
Email Service - SendGrid Integration

Handles email sending for bug reports and notifications.
Uses SendGrid API for reliable email delivery with attachment support.

Setup:
1. Sign up at https://sendgrid.com (100 emails/day free)
2. Create API key: Settings -> API Keys -> Create API Key
3. Add to .env: SENDGRID_API_KEY=SG.xxx
4. Verify sender email in SendGrid dashboard
"""

import base64
import os
from typing import Optional

from app.core.logging import logger
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Attachment,
    Content,
    Email,
    FileContent,
    FileName,
    FileType,
    Mail,
    To,
)


class EmailService:
    """
    Email service using SendGrid.
    Handles bug reports and system notifications.
    """
    
    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@yourdomain.com")
        self.support_email = os.getenv("SUPPORT_EMAIL", "support@yourdomain.com")
        
        if not self.api_key:
            logger.warning("⚠️ SENDGRID_API_KEY not found in environment. Email sending disabled.")
            self.client = None
        else:
            self.client = SendGridAPIClient(self.api_key)
            logger.info(f"✅ SendGrid initialized | From: {self.from_email}")
    
    def send_bug_report(
        self,
        user_id: str,
        description: str,
        conversation_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        user_agent: Optional[str] = None,
        attachment_data: Optional[bytes] = None,
        attachment_filename: Optional[str] = None,
        attachment_type: Optional[str] = None,
    ) -> bool:
        """
        Send bug report email to support team with optional file attachment.
        
        Args:
            user_id: User who reported the bug
            description: Bug description from user
            conversation_id: Optional conversation ID for context
            timestamp: Optional timestamp of the report
            user_agent: Optional browser user agent
            attachment_data: Optional file content as bytes
            attachment_filename: Optional filename for attachment
            attachment_type: Optional MIME type (image/*, video/*, application/pdf, application/zip, etc.)
        
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.client:
            logger.warning("📧 SendGrid not configured. Bug report not sent via email.")
            return False
        
        try:
            # Construct email subject
            subject = "🐞 Bug Report"
            if conversation_id:
                subject += f" - Conv: {conversation_id[:8]}..."
            if attachment_filename:
                # Determine file type emoji
                if attachment_type and attachment_type.startswith('video/'):
                    subject += " (with video 🎥)"
                elif attachment_type and attachment_type.startswith('image/'):
                    subject += " (with screenshot 📷)"
                elif attachment_type == 'application/pdf':
                    subject += " (with PDF 📄)"
                elif attachment_type and ('zip' in attachment_type or 'rar' in attachment_type or '7z' in attachment_type or 'tar' in attachment_type or 'gzip' in attachment_type):
                    subject += " (with archive 📦)"
                else:
                    subject += " (with attachment 📎)"
            
            # Construct HTML email body
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #dc2626; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                    .content {{ background-color: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; }}
                    .bug-description {{ background-color: white; padding: 15px; border-left: 4px solid #dc2626; margin: 15px 0; }}
                    .details {{ background-color: #f3f4f6; padding: 15px; border-radius: 4px; margin: 15px 0; }}
                    .details-table {{ width: 100%; border-collapse: collapse; }}
                    .details-table td {{ padding: 8px; border-bottom: 1px solid #d1d5db; }}
                    .details-table td:first-child {{ font-weight: bold; width: 40%; }}
                    code {{ background-color: #e5e7eb; padding: 2px 6px; border-radius: 3px; font-family: monospace; }}
                    .attachment-notice {{ background-color: #dbeafe; padding: 10px; border-left: 4px solid #3b82f6; margin: 15px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin: 0;">🐞 Bug Report</h1>
                    </div>
                    <div class="content">
                        <h2>Bug Description</h2>
                        <div class="bug-description">
                            {description.replace('\n', '<br>')}
                        </div>
                        
                        {f'<div class="attachment-notice">📎 <strong>Attachment Included:</strong> {attachment_filename} ({attachment_type or "unknown type"})</div>' if attachment_filename else ''}
                        
                        <h3>Technical Details</h3>
                        <div class="details">
                            <table class="details-table">
                                <tr>
                                    <td>User ID</td>
                                    <td><code>{user_id}</code></td>
                                </tr>
                                <tr>
                                    <td>Conversation ID</td>
                                    <td><code>{conversation_id or 'N/A'}</code></td>
                                </tr>
                                <tr>
                                    <td>Timestamp</td>
                                    <td>{timestamp or 'N/A'}</td>
                                </tr>
                                <tr>
                                    <td>User Agent</td>
                                    <td style="font-size: 12px;">{user_agent or 'N/A'}</td>
                                </tr>
                            </table>
                        </div>
                        
                        <p style="margin-top: 20px; padding: 15px; background-color: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 4px;">
                            <strong>Action Required:</strong> Review this bug report and investigate the issue. 
                            Check Firestore for the conversation history if Conversation ID is provided.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text fallback
            attachment_notice = f"\n\nAttachment: {attachment_filename}" if attachment_filename else ""
            plain_text = f"""
Bug Report

Bug Description:
{description}
{attachment_notice}

---
Technical Details:
- User ID: {user_id}
- Conversation ID: {conversation_id or 'N/A'}
- Timestamp: {timestamp or 'N/A'}
- User Agent: {user_agent or 'N/A'}

---
Action Required: Review this bug report and investigate the issue.
            """
            
            # Create SendGrid message
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=To(self.support_email),
                subject=subject,
                plain_text_content=Content("text/plain", plain_text),
                html_content=Content("text/html", html_content),
            )
            
            # Add attachment if provided
            if attachment_data and attachment_filename:
                # Encode file to base64
                encoded_file = base64.b64encode(attachment_data).decode()
                
                # Create attachment object
                attached_file = Attachment(
                    FileContent(encoded_file),
                    FileName(attachment_filename),
                    FileType(attachment_type or "application/octet-stream"),
                )
                message.attachment = attached_file
                
                logger.info(f"📎 Attachment added to email | Name: {attachment_filename} | Type: {attachment_type}")
            
            # Send email
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                attachment_log = f" | 📎 {attachment_filename}" if attachment_filename else ""
                logger.bind(EMAIL=True).info(
                    f"✅ Bug report email sent | To: {self.support_email} | Conv: {conversation_id or 'N/A'}{attachment_log}"
                )
                return True
            else:
                error_body = response.body.decode('utf-8') if response.body else 'No body'
                logger.error(
                    f"❌ SendGrid error | Status: {response.status_code} | Body: {error_body}"
                )
                if response.status_code == 403:
                    logger.warning(
                        "⚠️ SendGrid 403: Check if sender email is verified in SendGrid dashboard!"
                    )
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to send bug report email: {str(e)} | Type: {type(e).__name__}")
            return False


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """
    Get or create email service singleton instance.
    FastAPI dependency injection compatible.
    """
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
