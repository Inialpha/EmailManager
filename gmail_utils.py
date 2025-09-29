"""
Gmail API utility functions for fetching emails.
"""
import os
import logging
import pickle
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailFetcher:
    """Handles Gmail API operations for fetching emails."""
    
    def __init__(self):
        self.credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials.json')
        self.token_path = os.getenv('GMAIL_TOKEN_PATH', 'token.json')
        self.service = None
        
    def _authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth2.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                logger.error(f"Error loading existing token: {e}")
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Error refreshing token: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_path):
                    logger.error(f"Gmail credentials file not found: {self.credentials_path}")
                    return False
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    logger.error(f"Error during OAuth flow: {e}")
                    return False
            
            # Save the credentials for the next run
            try:
                with open(self.token_path, 'wb') as token:
                    pickle.dump(creds, token)
            except Exception as e:
                logger.error(f"Error saving token: {e}")
        
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail API authentication successful")
            return True
        except Exception as e:
            logger.error(f"Error building Gmail service: {e}")
            return False
    
    def fetch_recent_emails(self, hours: int = 24) -> List[Dict]:
        """
        Fetch emails from the last N hours.
        
        Args:
            hours: Number of hours to look back (default: 24)
            
        Returns:
            List[Dict]: List of email data with subject and snippet
        """
        if not self.service and not self._authenticate():
            logger.error("Gmail authentication failed")
            return []
        
        try:
            # Calculate the date for filtering emails
            since_date = datetime.utcnow() - timedelta(hours=hours)
            since_date_str = since_date.strftime('%Y/%m/%d')
            
            # Search for emails
            query = f'after:{since_date_str}'
            logger.info(f"Searching for emails with query: {query}")
            
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=100  # Limit to prevent excessive API calls
            ).execute()
            
            messages = results.get('messages', [])
            logger.info(f"Found {len(messages)} messages")
            
            emails = []
            
            for message in messages:
                try:
                    # Get message details
                    msg = self.service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='metadata',
                        metadataHeaders=['Subject', 'From', 'Date']
                    ).execute()
                    
                    # Extract subject and snippet
                    headers = msg.get('payload', {}).get('headers', [])
                    subject = 'No Subject'
                    sender = 'Unknown Sender'
                    
                    for header in headers:
                        if header['name'] == 'Subject':
                            subject = header['value']
                        elif header['name'] == 'From':
                            sender = header['value']
                    
                    snippet = msg.get('snippet', 'No content available')
                    
                    emails.append({
                        'subject': subject,
                        'snippet': snippet,
                        'sender': sender,
                        'message_id': message['id']
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing message {message['id']}: {e}")
                    continue
            
            logger.info(f"Successfully processed {len(emails)} emails")
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []
    
    def get_email_content(self, message_id: str) -> Optional[str]:
        """
        Get full email content for a specific message.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Optional[str]: Email content or None if failed
        """
        if not self.service:
            return None
            
        try:
            msg = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract email body (simplified - handles plain text)
            payload = msg.get('payload', {})
            
            if 'parts' in payload:
                # Multi-part message
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain':
                        data = part.get('body', {}).get('data')
                        if data:
                            import base64
                            return base64.urlsafe_b64decode(data).decode('utf-8')
            else:
                # Single-part message
                if payload.get('mimeType') == 'text/plain':
                    data = payload.get('body', {}).get('data')
                    if data:
                        import base64
                        return base64.urlsafe_b64decode(data).decode('utf-8')
            
            # Fallback to snippet
            return msg.get('snippet', '')
            
        except Exception as e:
            logger.error(f"Error getting email content: {e}")
            return None


# Global Gmail fetcher instance
gmail_fetcher = GmailFetcher()