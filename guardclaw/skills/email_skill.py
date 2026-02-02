"""
Email skill - send emails via SMTP.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
from .base import Skill


class EmailSkill(Skill):
    """Send emails using SMTP"""
    
    def __init__(self):
        super().__init__(
            name="send_email",
            description="Send emails via SMTP",
            capabilities=["network", "email"]
        )
    
    def execute(
        self,
        to: str,
        subject: str,
        body: str,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send an email.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            smtp_server: SMTP server address
            smtp_port: SMTP port
            
        Returns:
            Dict with success status
        """
        params = {
            "to": to,
            "subject": subject,
            "smtp_server": smtp_server
        }
        
        try:
            # Get credentials from kwargs (injected by agent)
            smtp_username = kwargs.get("smtp_username")
            smtp_password = kwargs.get("smtp_password")
            
            if not smtp_username or not smtp_password:
                raise ValueError("SMTP credentials not provided")
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = to
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            result = {
                "success": True,
                "result": f"Email sent to {to}",
                "to": to,
                "subject": subject
            }
        
        except Exception as e:
            result = {
                "success": False,
                "result": None,
                "error": str(e)
            }
        
        # Log execution
        self.log_execution(params, result)
        
        return result
