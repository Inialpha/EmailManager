"""
Unit tests for refactored email report functionality.
Tests the new credential-setting methods and parameter passing.
Run with: python -m pytest test_refactored_email.py -v
"""
import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock

# Mock environment variables before importing modules
os.environ["EMAIL_ADDRESS"] = "test@example.com"
os.environ["EMAIL_PASSWORD"] = "test_password"

from email_utils import EmailSender
from mail_utils.sender import GmailManager


class TestEmailSenderCredentials:
    """Test EmailSender credential management."""
    
    def test_set_credentials(self):
        """Test that set_credentials updates email credentials."""
        sender = EmailSender()
        
        # Set new credentials
        test_email = "test@example.com"
        test_password = "test_password_123"
        sender.set_credentials(test_email, test_password)
        
        # Verify credentials were updated
        assert sender.email_address == test_email
        assert sender.email_password == test_password
    
    def test_set_credentials_multiple_times(self):
        """Test that credentials can be updated multiple times."""
        sender = EmailSender()
        
        # Set first credentials
        sender.set_credentials("first@example.com", "password1")
        assert sender.email_address == "first@example.com"
        assert sender.email_password == "password1"
        
        # Update to second credentials
        sender.set_credentials("second@example.com", "password2")
        assert sender.email_address == "second@example.com"
        assert sender.email_password == "password2"


class TestGmailManagerCredentials:
    """Test GmailManager credential management."""
    
    @patch.dict(os.environ, {"EMAIL_ADDRESS": "init@example.com", "EMAIL_PASSWORD": "init_pass"})
    def test_set_credentials(self):
        """Test that set_credentials updates Gmail credentials."""
        manager = GmailManager()
        
        # Set new credentials
        test_email = "test@gmail.com"
        test_password = "test_app_password"
        manager.set_credentials(test_email, test_password)
        
        # Verify credentials were updated
        assert manager.email == test_email
        assert manager.app_password == test_password
    
    @patch.dict(os.environ, {"EMAIL_ADDRESS": "init@example.com", "EMAIL_PASSWORD": "init_pass"})
    def test_set_credentials_multiple_times(self):
        """Test that credentials can be updated multiple times."""
        manager = GmailManager()
        
        # Set first credentials
        manager.set_credentials("first@gmail.com", "password1")
        assert manager.email == "first@gmail.com"
        assert manager.app_password == "password1"
        
        # Update to second credentials
        manager.set_credentials("second@gmail.com", "password2")
        assert manager.email == "second@gmail.com"
        assert manager.app_password == "password2"


class TestDailyEmailReportForMultipleRecipients:
    """Test the refactored daily_email_report_for_multiple_recipients function."""
    
    @pytest.mark.asyncio
    @patch('main.daily_email_report')
    @patch.dict(os.environ, {
        "INIMFONEBONG001_PASSWORD": "password123",
    })
    async def test_calls_daily_email_report_with_credentials(self, mock_daily_report):
        """Test that daily_email_report is called with correct credentials."""
        from main import daily_email_report_for_multiple_recipients
        
        # Call the function
        await daily_email_report_for_multiple_recipients()
        
        # Verify daily_email_report was called with correct parameters
        mock_daily_report.assert_called_once_with(
            "inimfonebong001@gmail.com",
            "password123"
        )
    
    @pytest.mark.asyncio
    @patch('main.daily_email_report')
    @patch('main.logger')
    @patch.dict(os.environ, {}, clear=True)
    async def test_skips_recipient_with_missing_password(self, mock_logger, mock_daily_report):
        """Test that recipients with missing passwords are skipped with error logging."""
        from main import daily_email_report_for_multiple_recipients
        
        # Call the function (no password set for INIMFONEBONG001)
        await daily_email_report_for_multiple_recipients()
        
        # Verify daily_email_report was NOT called
        mock_daily_report.assert_not_called()
        
        # Verify error was logged
        mock_logger.error.assert_called()
        error_call_args = str(mock_logger.error.call_args)
        assert "No password found" in error_call_args
        assert "INIMFONEBONG001_PASSWORD" in error_call_args


class TestDailyEmailReport:
    """Test the refactored daily_email_report function."""
    
    @pytest.mark.asyncio
    @patch('main.email_sender')
    @patch('main.gmail_manager')
    @patch('main.email_summarizer')
    async def test_sets_credentials_before_fetching(self, mock_summarizer, mock_gmail, mock_sender):
        """Test that credentials are set before fetching emails."""
        from main import daily_email_report
        
        # Setup mocks
        mock_gmail.fetch_recent_emails.return_value = []
        mock_sender.send_html_report.return_value = {"success": True, "message": "Sent"}
        mock_summarizer.summarize_emails_batch.return_value = []
        
        # Call the function
        test_email = "test@gmail.com"
        test_password = "test_password"
        await daily_email_report(test_email, test_password)
        
        # Verify credentials were set on both managers
        mock_sender.set_credentials.assert_called_once_with(test_email, test_password)
        mock_gmail.set_credentials.assert_called_once_with(test_email, test_password)
        
        # Verify fetch was called after credentials were set
        mock_gmail.fetch_recent_emails.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
