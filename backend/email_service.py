import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

class EmailService:
    def __init__(self):
        # Load email settings from database first, fall back to environment variables
        self._load_settings()
    
    def _load_settings(self):
        """Load email settings from database or environment variables"""
        try:
            from .api.settings import load_settings
            settings = load_settings()
            email_settings = settings.get('email_settings', {})
            
            # Use database settings if available, otherwise fall back to environment variables
            self.smtp_server = email_settings.get('smtp_server') or os.getenv("SMTP_SERVER", "mail.smtp2go.com")
            self.smtp_port = int(email_settings.get('smtp_port') or os.getenv("SMTP_PORT", "2525"))
            self.smtp_username = email_settings.get('smtp_username') or os.getenv("SMTP_USERNAME")
            self.smtp_password = email_settings.get('smtp_password') or os.getenv("SMTP_PASSWORD")
            self.from_email = email_settings.get('from_email') or os.getenv("FROM_EMAIL", "pyscheduler@example.com")
            
        except Exception:
            # Fall back to environment variables if database load fails
            self.smtp_server = os.getenv("SMTP_SERVER", "mail.smtp2go.com")
            self.smtp_port = int(os.getenv("SMTP_PORT", "2525"))
            self.smtp_username = os.getenv("SMTP_USERNAME")
            self.smtp_password = os.getenv("SMTP_PASSWORD")
            self.from_email = os.getenv("FROM_EMAIL", "pyscheduler@example.com")
        
        self.enabled = bool(self.smtp_server and self.smtp_username and self.smtp_password)
    
    def send_script_notification(self, script_name: str, status: str, output: str, recipients: str):
        """Send email notification for script execution"""
        # Reload settings each time to ensure we have the latest database configuration
        self._load_settings()
        
        print(f"[EMAIL] Attempting to send notification for script: {script_name}")
        print(f"[EMAIL] Status: {status}")
        print(f"[EMAIL] Recipients: {recipients}")
        print(f"[EMAIL] Email enabled: {self.enabled}")
        print(f"[EMAIL] SMTP settings: {self.smtp_server}:{self.smtp_port}")
        
        if not self.enabled or not recipients:
            print(f"[EMAIL] Email service not enabled or no recipients. Enabled: {self.enabled}, Recipients: {recipients}")
            return False
        
        subject = f"PyScheduler: {script_name} - {status.title()}"
        
        # Create email body
        body = f"""
Script: {script_name}
Status: {status.title()}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Output:
{output[:2000]}{'...' if len(output) > 2000 else ''}

---
PyScheduler Notification
        """
        
        # Send to each recipient
        success_count = 0
        for recipient in recipients.split(","):
            recipient = recipient.strip()
            if recipient:
                try:
                    if self._send_email(recipient, subject, body):
                        success_count += 1
                except Exception as e:
                    print(f"Failed to send email to {recipient}: {e}")
        
        return success_count > 0
    
    def _send_email(self, to: str, subject: str, body: str) -> bool:
        """Send email via SMTP"""
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"SMTP error: {e}")
            return False
    
    def test_connection(self) -> dict:
        """Test SMTP connection"""
        if not self.enabled:
            return {"success": False, "error": "Email service not configured"}
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
            
            return {"success": True, "message": "SMTP connection successful"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

# Global email service instance
email_service = EmailService()

def send_script_notification(script_name: str, status: str, output: str, recipients: str) -> bool:
    """Send script notification email"""
    return email_service.send_script_notification(script_name, status, output, recipients)

def test_email_connection() -> dict:
    """Test email connection"""
    return email_service.test_connection()