"""
Azure Communication Services Email Service
Handles sending emails using Azure Communication Services
"""
from typing import Optional
from django.conf import settings
from azure.communication.email import EmailClient


class AzureEmailService:
    """Service for sending emails via Azure Communication Services"""

    def __init__(self):
        """Initialize the Azure Email Client"""
        self.connection_string = settings.AZURE_EMAIL_CONNECTION_STRING
        self.sender_address = settings.AZURE_EMAIL_SENDER
        
        if not self.connection_string:
            raise ValueError("AZURE_EMAIL_CONNECTION_STRING is not configured")
        
        self.client = EmailClient.from_connection_string(self.connection_string)

    def send_email(
        self, 
        recipient_email: str, 
        subject: str, 
        html_content: str,
        plain_text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email using Azure Communication Services
        
        Args:
            recipient_email: The recipient's email address
            subject: Email subject line
            html_content: HTML content of the email
            plain_text_content: Plain text fallback (optional)
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Create the email message using the dictionary format
            message = {
                "senderAddress": self.sender_address,
                "recipients": {
                    "to": [{"address": recipient_email}]
                },
                "content": {
                    "subject": subject,
                    "plainText": plain_text_content or "Please view this email in HTML format.",
                    "html": html_content
                }
            }

            # Send the email
            poller = self.client.begin_send(message)
            result = poller.result()
            
            # Check if the email was sent successfully
            if result:
                print(f"Email sent successfully to {recipient_email}. Message ID: {result.get('id', 'unknown')}")
                return True
            else:
                print(f"Failed to send email to {recipient_email}")
                return False
                
        except Exception as e:
            print(f"Error sending email via Azure Communication Services: {e}")
            return False

    def send_receipt_email(
        self,
        recipient_email: str,
        order_id: int,
        html_content: str,
        total_amount: float
    ) -> bool:
        """
        Send a receipt email to a customer
        
        Args:
            recipient_email: Customer's email address
            order_id: Order ID number
            html_content: Rendered HTML receipt
            total_amount: Order total amount
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        subject = f'Your Panda Express Receipt - Order #{order_id}'
        plain_text = (
            f'Thank you for your order!\n\n'
            f'Order #{order_id}\n'
            f'Total: ${total_amount:.2f}\n\n'
            f'Please view this email in HTML format to see your full receipt.'
        )
        
        return self.send_email(
            recipient_email=recipient_email,
            subject=subject,
            html_content=html_content,
            plain_text_content=plain_text
        )
