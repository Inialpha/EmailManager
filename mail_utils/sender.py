"""
Gmail utility functions for fetching and sending emails using IMAP/SMTP with app password.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from imap_tools import MailBox, AND
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class GmailManager:
    """Handles Gmail operations for fetching and sending emails via IMAP/SMTP."""

    def __init__(self):
        self.email = os.getenv("EMAIL_ADDRESS")
        self.app_password = os.getenv("EMAIL_PASSWORD")
        self.imap_server = "imap.gmail.com"
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 465

        if not self.email or not self.app_password:
            raise ValueError("Missing GMAIL_USER or GMAIL_APP_PASSWORD environment variables")

    def fetch_recent_emails(self, hours: int = 24) -> List[Dict]:
        """
        Fetch emails from the last N hours using IMAP.

        Args:
            hours: Number of hours to look back (default: 24)

        Returns:
            List[Dict]: List of emails with subject, snippet, sender, date
        """
        try:
            since_time = datetime.utcnow() - timedelta(hours=hours)
            emails = []

            with MailBox(self.imap_server).login(self.email, self.app_password) as mailbox:
                messages = mailbox.fetch(
                    AND(date_gte=since_time.date()),
                    limit=50,
                    reverse=True
                )

                for msg in messages:
                    snippet = (msg.text or msg.html or "")[:120].replace("\n", " ")
                    emails.append({
                        "subject": msg.subject or "No Subject",
                        "snippet": snippet,
                        "sender": msg.from_,
                        "date": msg.date_str,
                        "uid": msg.uid
                    })

            logger.info(f"Fetched {len(emails)} recent emails")
            return emails

        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []

    def get_email_content(self, uid: str) -> Optional[str]:
        """
        Get full email body by IMAP UID.

        Args:
            uid: IMAP UID of the email

        Returns:
            str or None: Full plain-text email body
        """
        try:
            with MailBox(self.imap_server).login(self.email, self.app_password) as mailbox:
                msg = mailbox.fetch(AND(uid=uid), limit=1)
                for m in msg:
                    return m.text or m.html or ""
            return None
        except Exception as e:
            logger.error(f"Error fetching email content for UID {uid}: {e}")
            return None

    def send_email(self, to: str, subject: str, body: str) -> bool:
        """
        Send an email using SMTP and app password.

        Args:
            to: Receiver email
            subject: Subject line
            body: Message body (plain text)

        Returns:
            bool: True if sent successfully
        """
        try:
            msg = MIMEMultipart()
            msg["From"] = self.email
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.email, self.app_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to}")
            return True
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False


gmail_manager = GmailManager()
