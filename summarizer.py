"""
Email summarization using LangChain LLMs.
"""
import os
import logging
from typing import List, Dict, Optional
from langchain.schema import HumanMessage
from langchain.llms.base import BaseLLM

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailSummarizer:
    """Handles email summarization using LangChain LLMs."""
    
    def __init__(self):
        self.llm = None
        self._initialize_llm()
    
    def _initialize_llm(self) -> None:
        """Initialize the LLM based on available API keys."""
        openai_key = os.getenv('OPENAI_API_KEY')
        groq_key = os.getenv('GROQ_API_KEY')
        
        if openai_key:
            try:
                from langchain_openai import ChatOpenAI
                self.llm = ChatOpenAI(
                    model="gpt-3.5-turbo",
                    temperature=0.3,
                    api_key=openai_key
                )
                logger.info("Initialized OpenAI LLM")
                return
            except ImportError:
                logger.warning("OpenAI package not available, trying Groq")
            except Exception as e:
                logger.error(f"Error initializing OpenAI LLM: {e}")
        
        if groq_key:
            try:
                from langchain_groq import ChatGroq
                self.llm = ChatGroq(
                    model="mixtral-8x7b-32768",
                    temperature=0.3,
                    groq_api_key=groq_key
                )
                logger.info("Initialized Groq LLM")
                return
            except ImportError:
                logger.warning("Groq package not available")
            except Exception as e:
                logger.error(f"Error initializing Groq LLM: {e}")
        
        logger.error("No LLM could be initialized. Please check your API keys.")
    
    def summarize_email(self, subject: str, content: str) -> str:
        """
        Summarize a single email using the LLM.
        
        Args:
            subject: Email subject line
            content: Email content/snippet
            
        Returns:
            str: Summarized email content
        """
        if not self.llm:
            logger.warning("No LLM available for summarization")
            return f"Unable to summarize - LLM not available. Original content: {content[:200]}..."
        
        try:
            # Create a prompt for summarization
            prompt = f"""
            Please provide a concise summary of the following email in 2-3 sentences.
            Focus on the main purpose, key information, and any action items.
            
            Subject: {subject}
            Content: {content}
            
            Summary:
            """
            
            # Use the LLM to generate summary
            if hasattr(self.llm, 'invoke'):
                # For newer LangChain versions
                response = self.llm.invoke([HumanMessage(content=prompt)])
                summary = response.content.strip()
            else:
                # For older versions
                summary = self.llm(prompt).strip()
            
            # Clean up the summary
            summary = summary.replace("Summary:", "").strip()
            
            logger.info(f"Generated summary for email: {subject[:50]}...")
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing email: {e}")
            # Fallback to truncated original content
            return f"Summarization failed. Original content: {content[:200]}..."
    
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
                    'subject': subject,
                    'summary': summary
                })
                
            except Exception as e:
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