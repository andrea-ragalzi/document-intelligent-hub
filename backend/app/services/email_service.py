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

# Constants for repeated literals
CONTENT_TYPE_TEXT_PLAIN = "text/plain"
CONTENT_TYPE_TEXT_HTML = "text/html"
ERROR_NO_BODY = "No body"
ERROR_SENDGRID_403_MESSAGE = "⚠️ SendGrid 403: Check if sender email is verified in SendGrid dashboard!"


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
                plain_text_content=Content(CONTENT_TYPE_TEXT_PLAIN, plain_text),
                html_content=Content(CONTENT_TYPE_TEXT_HTML, html_content),
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
                error_body = response.body.decode('utf-8') if response.body else ERROR_NO_BODY
                logger.error(
                    f"❌ SendGrid error | Status: {response.status_code} | Body: {error_body}"
                )
                if response.status_code == 403:
                    logger.warning(ERROR_SENDGRID_403_MESSAGE)
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to send bug report email: {str(e)} | Type: {type(e).__name__}")
            return False

    def send_feedback(
        self,
        user_id: str,
        rating: int,
        message: Optional[str] = None,
        conversation_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """
        Send user feedback email to support team with star rating.
        
        Args:
            user_id: User who provided feedback
            rating: Star rating from 1 to 5
            message: Optional feedback message
            conversation_id: Optional conversation ID for context
            timestamp: Optional timestamp of the feedback
            user_agent: Optional browser user agent
        
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.client:
            logger.warning("📧 SendGrid not configured. Feedback not sent via email.")
            return False
        
        try:
            # Generate star rating visual (⭐⭐⭐⭐⭐ or ⭐⭐⭐☆☆)
            star_visual = "⭐" * rating + "☆" * (5 - rating)
            
            # Determine feedback sentiment
            if rating >= 4.0:
                sentiment = "Positive"
                sentiment_color = "#16a34a"  # Green
                emoji = "😊"
            elif rating >= 3.0:
                sentiment = "Neutral"
                sentiment_color = "#eab308"  # Yellow
                emoji = "😐"
            else:
                sentiment = "Negative"
                sentiment_color = "#dc2626"  # Red
                emoji = "😞"
            
            # Construct email subject
            subject = f"{emoji} User Feedback: {rating}/5 stars"
            if conversation_id:
                subject += f" - Conv: {conversation_id[:8]}..."
            
            # Construct HTML email body
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: {sentiment_color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }}
                    .rating {{ font-size: 32px; margin: 10px 0; }}
                    .content {{ background-color: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; }}
                    .feedback-message {{ background-color: white; padding: 15px; border-left: 4px solid {sentiment_color}; margin: 15px 0; }}
                    .details {{ background-color: #f3f4f6; padding: 15px; border-radius: 4px; margin: 15px 0; }}
                    .details-table {{ width: 100%; border-collapse: collapse; }}
                    .details-table td {{ padding: 8px; border-bottom: 1px solid #d1d5db; }}
                    .details-table td:first-child {{ font-weight: bold; width: 40%; }}
                    code {{ background-color: #e5e7eb; padding: 2px 6px; border-radius: 3px; font-family: monospace; }}
                    .sentiment-badge {{ display: inline-block; padding: 5px 15px; border-radius: 20px; background-color: {sentiment_color}; color: white; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin: 0;">{emoji} User Feedback</h1>
                        <div class="rating">{star_visual}</div>
                        <h2 style="margin: 10px 0 0 0;">{rating} / 5</h2>
                        <span class="sentiment-badge">{sentiment}</span>
                    </div>
                    <div class="content">
                        {f'<h2>Feedback Message</h2><div class="feedback-message">{message.replace(chr(10), "<br>")}</div>' if message else '<p style="text-align: center; color: #6b7280; font-style: italic;">No message provided</p>'}
                        
                        <h3>User Details</h3>
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
                                    <td>Rating</td>
                                    <td><strong>{rating} / 5.0</strong> ({sentiment})</td>
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
                        
                        <p style="margin-top: 20px; padding: 15px; background-color: #dbeafe; border-left: 4px solid #3b82f6; border-radius: 4px;">
                            <strong>📊 Action:</strong> Review this feedback to improve user experience and system performance.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text fallback
            message_text = f"\n\nMessage: {message}" if message else "\n\n(No message provided)"
            plain_text = f"""
User Feedback

Rating: {rating} / 5 ({sentiment})
Stars: {star_visual}
{message_text}

---
User Details:
- User ID: {user_id}
- Conversation ID: {conversation_id or 'N/A'}
- Timestamp: {timestamp or 'N/A'}
- User Agent: {user_agent or 'N/A'}

---
Action: Review this feedback to improve user experience and system performance.
            """
            
            # Create SendGrid message
            email_message = Mail(
                from_email=Email(self.from_email),
                to_emails=To(self.support_email),
                subject=subject,
                plain_text_content=Content(CONTENT_TYPE_TEXT_PLAIN, plain_text),
                html_content=Content(CONTENT_TYPE_TEXT_HTML, html_content),
            )
            
            # Send email
            response = self.client.send(email_message)
            
            if response.status_code in [200, 201, 202]:
                logger.bind(EMAIL=True).info(
                    f"✅ Feedback email sent | To: {self.support_email} | Rating: {rating}/5 | Conv: {conversation_id or 'N/A'}"
                )
                return True
            else:
                error_body = response.body.decode('utf-8') if response.body else ERROR_NO_BODY
                logger.error(
                    f"❌ SendGrid error | Status: {response.status_code} | Body: {error_body}"
                )
                if response.status_code == 403:
                    logger.warning(ERROR_SENDGRID_403_MESSAGE)
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to send feedback email: {str(e)} | Type: {type(e).__name__}")
            return False

    def send_invitation_request(
        self,
        first_name: str,
        last_name: str,
        email: str,
    ) -> bool:
        """
        Send invitation code request email to support team.
        
        Args:
            first_name: User's first name
            last_name: User's last name
            email: User's email address
        
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.client:
            logger.warning("📧 SendGrid not configured. Invitation request not sent via email.")
            return False
        
        try:
            # Email subject
            subject = f"🎫 Invitation Code Request from {first_name} {last_name}"
            
            # Plain text content
            plain_text = f"""
Invitation Code Request
========================

A user has requested an invitation code.

User Details:
- Name: {first_name} {last_name}
- Email: {email}

Action Required:
Please review this request and send an invitation code to the user if appropriate.

---
Automated email from Document Intelligent Hub
            """
            
            # HTML content
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px; }}
        .user-info {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea; }}
        .info-row {{ margin: 10px 0; }}
        .label {{ font-weight: bold; color: #667eea; }}
        .action {{ background: #fef3c7; padding: 15px; border-radius: 8px; border-left: 4px solid #f59e0b; margin: 20px 0; }}
        .footer {{ text-align: center; color: #6b7280; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin: 0;">🎫 Invitation Code Request</h2>
        </div>
        <div class="content">
            <p>A user has requested an invitation code for Document Intelligent Hub.</p>
            
            <div class="user-info">
                <h3 style="margin-top: 0; color: #667eea;">User Details</h3>
                <div class="info-row">
                    <span class="label">Name:</span> {first_name} {last_name}
                </div>
                <div class="info-row">
                    <span class="label">Email:</span> {email}
                </div>
            </div>
            
            <div class="action">
                <h4 style="margin-top: 0; color: #f59e0b;">⚡ Action Required</h4>
                <p style="margin: 0;">Please review this request and send an invitation code to the user if appropriate.</p>
            </div>
            
            <div class="footer">
                <p>Automated email from Document Intelligent Hub</p>
            </div>
        </div>
    </div>
</body>
</html>
            """
            
            # Create SendGrid message
            email_message = Mail(
                from_email=Email(self.from_email),
                to_emails=To(self.support_email),
                subject=subject,
                plain_text_content=Content(CONTENT_TYPE_TEXT_PLAIN, plain_text),
                html_content=Content(CONTENT_TYPE_TEXT_HTML, html_content),
            )
            
            # Send email
            response = self.client.send(email_message)
            
            if response.status_code in [200, 201, 202]:
                logger.bind(EMAIL=True).info(
                    f"✅ Invitation request email sent | To: {self.support_email} | User: {first_name} {last_name} ({email})"
                )
                return True
            else:
                error_body = response.body.decode('utf-8') if response.body else ERROR_NO_BODY
                logger.error(
                    f"❌ SendGrid error | Status: {response.status_code} | Body: {error_body}"
                )
                if response.status_code == 403:
                    logger.warning(ERROR_SENDGRID_403_MESSAGE)
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to send invitation request email: {str(e)} | Type: {type(e).__name__}")
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
