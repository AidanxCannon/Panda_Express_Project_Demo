"""
Custom Django Email Backend using Azure Communication Services
"""
from django.core.mail.backends.base import BaseEmailBackend
from core.services.azure_email_service import AzureEmailService


class AzureEmailBackend(BaseEmailBackend):
    """
    Email backend that sends emails using Azure Communication Services
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.azure_service = None
    
    def open(self):
        """Open a connection (initialize Azure service if needed)"""
        if self.azure_service is None:
            try:
                self.azure_service = AzureEmailService()
                return True
            except Exception as e:
                if self.fail_silently:
                    return False
                raise
        return True
    
    def close(self):
        """Close connection (nothing to do for Azure)"""
        pass
    
    def send_messages(self, email_messages):
        """
        Send one or more EmailMessage objects and return the number of email
        messages sent.
        """
        if not email_messages:
            return 0
        
        if not self.open():
            return 0
        
        num_sent = 0
        for message in email_messages:
            sent = self._send(message)
            if sent:
                num_sent += 1
        
        return num_sent
    
    def _send(self, email_message):
        """Send a single EmailMessage"""
        try:
            # Get recipients
            if not email_message.to:
                return False
            
            recipient = email_message.to[0]  # Azure sends to one recipient at a time
            
            # Get email content
            subject = email_message.subject
            
            # Try to get HTML content from alternatives
            html_content = None
            if hasattr(email_message, 'alternatives') and email_message.alternatives:
                for content, mimetype in email_message.alternatives:
                    if mimetype == 'text/html':
                        html_content = content
                        break
            
            # If no HTML, use plain text body as HTML
            if not html_content:
                html_content = f"<html><body><pre>{email_message.body}</pre></body></html>"
            
            plain_text = email_message.body
            
            # Send via Azure
            success = self.azure_service.send_email(
                recipient_email=recipient,
                subject=subject,
                html_content=html_content,
                plain_text_content=plain_text
            )
            
            return success
            
        except Exception as e:
            if not self.fail_silently:
                raise
            return False
