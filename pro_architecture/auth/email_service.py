"""
Email service for sending magic link authentication emails via Mailgun.
"""
import requests
import os
from typing import Optional


class EmailService:
    """Service for sending emails via Mailgun API."""
    
    def __init__(self):
        self.api_key = os.environ.get("MAILGUN_API_KEY", "")
        self.domain = os.environ.get("MAILGUN_DOMAIN", "mg.hollywoodsignal.com")
        self.from_email = os.environ.get("MAILGUN_FROM_EMAIL", "Mandate Wizard <noreply@hollywoodsignal.com>")
        
        if not self.api_key:
            raise ValueError("MAILGUN_API_KEY environment variable is required")
        
        self.api_url = f"https://api.mailgun.net/v3/{self.domain}/messages"
    
    def send_magic_link(self, to_email: str, magic_link: str, name: Optional[str] = None) -> bool:
        """
        Send magic link authentication email.
        
        Args:
            to_email: Recipient email address
            magic_link: Full URL with authentication token
            name: Optional recipient name
            
        Returns:
            True if email sent successfully, False otherwise
        """
        display_name = name if name else to_email.split('@')[0]
        
        subject = "Sign in to Mandate Wizard"
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 28px;">Mandate Wizard</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0;">Strategic Intelligence for Hollywood Signal Subscribers</p>
    </div>
    
    <div style="background: white; padding: 40px 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
        <p style="font-size: 16px; margin-bottom: 20px;">Hi {display_name},</p>
        
        <p style="font-size: 16px; margin-bottom: 25px;">Click the button below to securely sign in to Mandate Wizard:</p>
        
        <div style="text-align: center; margin: 35px 0;">
            <a href="{magic_link}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 40px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 16px; display: inline-block; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">Sign In to Mandate Wizard</a>
        </div>
        
        <p style="font-size: 14px; color: #666; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
            This link will expire in <strong>15 minutes</strong> for security reasons.
        </p>
        
        <p style="font-size: 14px; color: #666; margin-top: 15px;">
            If you didn't request this email, you can safely ignore it.
        </p>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0; text-align: center;">
            <p style="font-size: 12px; color: #999; margin: 5px 0;">
                Mandate Wizard is exclusively for Hollywood Signal subscribers
            </p>
            <p style="font-size: 12px; color: #999; margin: 5px 0;">
                <a href="https://hollywood-signal.ghost.io" style="color: #667eea; text-decoration: none;">Learn more about Hollywood Signal</a>
            </p>
        </div>
    </div>
</body>
</html>
"""
        
        text_body = f"""
Hi {display_name},

Click the link below to sign in to Mandate Wizard:

{magic_link}

This link will expire in 15 minutes for security reasons.

If you didn't request this email, you can safely ignore it.

---
Mandate Wizard is exclusively for Hollywood Signal subscribers
Learn more: https://hollywood-signal.ghost.io
"""
        
        try:
            response = requests.post(
                self.api_url,
                auth=("api", self.api_key),
                data={
                    "from": self.from_email,
                    "to": to_email,
                    "subject": subject,
                    "text": text_body,
                    "html": html_body
                },
                timeout=10
            )
            
            response.raise_for_status()
            print(f"Magic link email sent to: {to_email}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to send email to {to_email}: {e}")
            return False
