"""
Email summarization using LangChain LLMs.
"""
import os
import logging
from typing import List, Dict, Optional

from groq import Groq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


import json
from groq import Groq


class EmailSummarizer:
    """Summarizes emails using Groq LLM and returns structured JSON."""

    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY")
        if not self.groq_key:
            logger.error("GROQ_API_KEY not found in environment variables.")
            self.client = None
        else:
            try:
                self.client = Groq(api_key=self.groq_key)
                logger.info("✅ Groq client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self.client = None

    def summarize_email(self, subject: str, content: str) -> dict:
        """
        Summarize a single email using the Groq LLM.

        Args:
            subject: Email subject line
            content: Email content/snippet

        Returns:
            dict: { "subject": <subject>, "summary": <summary> }
        """
        if not self.client:
            logger.warning("No Groq client available for summarization.")
            return {
                "subject": "No Subject",
                "summary": f"⚠️ Unable to summarize. Original content: {content[:200]}..."
            }

        try:
            prompt = f"""
You will receive the content of an email.
Your task is to provide a concise 3–6 sentence summary focusing on the main purpose, key points, and any action items.

Return ONLY a valid JSON object with the following structure:
{{
  "subject": "<email subject>",
  "summary": "<summary text>"
}}

Make sure the response is a valid JSON — no extra text or explanation.

Content: {content}
"""

            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful personal assistant that summarizes emails into concise structured JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_completion_tokens=300
            )

            raw_output = response.choices[0].message.content.strip()

            try:
                result = json.loads(raw_output)
                logger.info(f"🧠 Summary generated for: {subject[:50]}...")
                return result
            except json.JSONDecodeError:
                logger.warning("Model response was not valid JSON. Returning fallback.")
                return {"subject": "No subject", "summary": raw_output}

        except Exception as e:
            raise e
            logger.error(f"Error summarizing email: {e}")
            return {
                "subject": "No subject",
                "summary": f"⚠️ Summarization failed. Original content: {content[:200]}..."
            }








    def summarize_emails_batch(self, emails: List[Dict]) -> List[Dict]:
        """
        Summarize a batch of emails.
        
        Args:
            emails: List of email dictionaries with 'subject' and 'snippet' keys
            
        Returns:
            List[Dict]: List of email summaries with 'subject' and 'summary' keys
        """
        if not emails:
            logger.info("No emails to summarize")
            return []
        
        logger.info(f"Starting summarization of {len(emails)} emails")
        summaries = []
        
        for i, email in enumerate(emails, 1):
            try:
                subject = email.get('subject', 'No Subject')
                content = email.get('snippet', email.get('content', ''))
                
                logger.info(f"Summarizing email {i}/{len(emails)}: {subject[:50]}...")
                
                summary = self.summarize_email(subject, content)
                
                summaries.append({
                    'subject': summary.get("subject"),
                    'summary': summary.get("summary", "") 
                })
                
            except Exception as e:
                raise e
                logger.error(f"Error processing email {i}: {e}")
                # Add a fallback entry
                summaries.append({
                    'subject': email.get('subject', 'Error processing email'),
                    'summary': f"Error occurred during summarization: {str(e)}"
                })
        
        logger.info(f"Completed summarization of {len(summaries)} emails")
        return summaries
    
    def is_available(self) -> bool:
        """Check if the summarizer is properly initialized and available."""
        return self.llm is not None


# Global email summarizer instance
email_summarizer = EmailSummarizer()
