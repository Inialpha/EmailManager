"""
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

# Import our custom modules
from mail_utils.sender import gmail_manager
from email_utils import email_sender
from gmail_utils import gmail_fetcher
from summarizer import email_summarizer

# Load environment variables
load_dotenv()


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models for API
class EmailRequest(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

class EmailResponse(BaseModel):
    success: bool
    message: str

def daily_email_report(recipient_email: str, email_password: str):
    """
    Scheduled function to fetch emails, summarize them, and send a report.
    
    Args:
        recipient_email: Email address to send the report to (also used for fetching emails)
        email_password: Password/app password for the email account
    """
    try:
        logger.info(f"Starting daily email report generation for {recipient_email}...")
        
        # Set credentials for email sender and Gmail manager
        email_sender.set_credentials(recipient_email, email_password)
        gmail_manager.set_credentials(recipient_email, email_password)
        
        # Fetch recent emails from Gmail
        logger.info("Fetching emails from Gmail...")
        emails = gmail_manager.fetch_recent_emails(hours=24)
        
        if not emails:
            logger.info("No emails found in the last 24 hours")
            summaries = []
        else:
            logger.info(f"Found {len(emails)} emails, starting summarization...")
            summaries = email_summarizer.summarize_emails_batch(emails)
        report_data = {
            "date": datetime.utcnow().strftime("%B %d, %Y"),
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "total_emails": len(emails),
            "summaries": summaries
        }
        
        logger.info(f"Sending report to {recipient_email}")
        result = email_sender.send_html_report(recipient_email, report_data)
        
        if result["success"]:
            logger.info(f"Daily email report sent successfully to {recipient_email}")
        else:
            logger.error(f"Failed to send daily report to {recipient_email}: {result['message']}")
            
    except Exception as e:
        logger.error(f"Error in daily_email_report for {recipient_email}: {e}")


def daily_email_report_for_multiple_recipients():
    """
    Send daily email reports to multiple recipients.
    Each recipient gets their own report using their individual credentials.
    """
    recipients = ["inimfonebong001@gmail.com", "ebonginimfon8@gmail.com"] #"inimfonebong2023@gmail.com"
    for recipient in recipients:
        username = recipient.split("@")[0].upper()
        password = os.getenv(f"{username}_PASSWORD")
        
        if not password:
            logger.error(f"No password found for {recipient} (env var: {username}_PASSWORD). Skipping.")
            continue
        
        daily_email_report(recipient, password)

if __name__ == "__main__":
    logger.info(f"Starting Application")
    daily_email_report_for_multiple_recipients()
