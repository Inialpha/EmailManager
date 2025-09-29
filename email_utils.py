"""
Email utility functions for sending emails using SMTP.
"""
import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from jinja2 import Environment, FileSystemLoader

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailSender:
    """Handles email sending functionality using SMTP."""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_address = os.getenv('EMAIL_ADDRESS')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        
        # Set up Jinja2 environment for templates
        self.template_env = Environment(
            loader=FileSystemLoader('templates'),
            autoescape=True
        )
        
        if not self.email_address or not self.email_password:
            logger.warning("Email credentials not found in environment variables")
    
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        body: str, 
        is_html: bool = False,
        template_name: Optional[str] = None,
        template_vars: Optional[dict] = None
    ) -> dict:
        """
        Send an email with optional HTML template rendering.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text or HTML)
            is_html: Whether the body is HTML
            template_name: Optional Jinja2 template name
            template_vars: Variables for template rendering
            
        Returns:
            dict: Success/failure response
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Render template if provided
            if template_name and template_vars:
                try:
                    template = self.template_env.get_template(template_name)
                    rendered_body = template.render(**template_vars)
                    body = rendered_body
                    is_html = True
                except Exception as e:
                    logger.error(f"Template rendering failed: {e}")
                    return {
                        "success": False,
                        "message": f"Template rendering failed: {str(e)}"
                    }
            
            # Add body to message
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return {
                "success": True,
                "message": f"Email sent successfully to {to_email}"
            }
            
        except smtplib.SMTPAuthenticationError:
            error_msg = "SMTP authentication failed. Check email credentials."
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
            
        except smtplib.SMTPRecipientsRefused:
            error_msg = f"Invalid recipient email address: {to_email}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
            
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error occurred: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
            
        except Exception as e:
            error_msg = f"Unexpected error sending email: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    def send_html_report(self, to_email: str, report_data: dict) -> dict:
        """
        Send HTML email report using template.
        
        Args:
            to_email: Recipient email address
            report_data: Data for the report template
            
        Returns:
            dict: Success/failure response
        """
        return self.send_email(
            to_email=to_email,
            subject="Daily Email Summary Report",
            body="",  # Will be replaced by template
            template_name="summary_report.html",
            template_vars=report_data
        )


# Global email sender instance
email_sender = EmailSender()