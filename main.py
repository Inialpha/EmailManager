"""
FastAPI Email Automation App
Main application with API endpoints and scheduled tasks.
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

# Import our custom modules
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

# Global scheduler
scheduler = AsyncIOScheduler()

# Pydantic models for API
class EmailRequest(BaseModel):
    to_email: EmailStr
    subject: str
    body: str

class EmailResponse(BaseModel):
    success: bool
    message: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    # Startup
    logger.info("Starting Email Manager application...")
    
    # Start the scheduler
    scheduler.start()
    
    # Schedule the daily email fetcher
    scheduler.add_job(
        func=daily_email_report,
        trigger="interval",
        hours=24,
        id="daily_email_report",
        replace_existing=True
    )
    
    logger.info("Scheduler started - daily email reports will run every 24 hours")
    
    # Run once on startup (for testing)
    if os.getenv('DEBUG') == 'True':
        logger.info("Debug mode - scheduling initial report in 1 minute")
        scheduler.add_job(
            func=daily_email_report,
            trigger="interval",
            seconds=60,
            id="initial_report",
            max_instances=1
        )
    
    yield
    
    # Shutdown
    logger.info("Shutting down Email Manager application...")
    scheduler.shutdown()

# Create FastAPI app
app = FastAPI(
    title="Email Manager API",
    description="FastAPI Email Automation App with Gmail fetching and LLM summarization",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with API information."""
    return {
        "message": "Email Manager API",
        "version": "1.0.0",
        "endpoints": {
            "send_email": "/send-email/",
            "health": "/health",
            "status": "/status"
        }
    }

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "email_sender": bool(email_sender.email_address and email_sender.email_password),
            "summarizer": email_summarizer.is_available()
        }
    }

@app.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get application status and configuration."""
    return {
        "scheduler_running": scheduler.running,
        "scheduled_jobs": [
            {
                "id": job.id,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
            for job in scheduler.get_jobs()
        ],
        "email_configured": bool(email_sender.email_address),
        "llm_available": email_summarizer.is_available()
    }

@app.post("/send-email/", response_model=EmailResponse)
async def send_email(email_request: EmailRequest) -> EmailResponse:
    """
    Send an email using the configured SMTP settings.
    
    Args:
        email_request: Email data including recipient, subject, and body
        
    Returns:
        EmailResponse: Success/failure response
    """
    try:
        logger.info(f"Received email request to {email_request.to_email}")
        
        # Send email using template
        result = email_sender.send_email(
            to_email=str(email_request.to_email),
            subject=email_request.subject,
            body="",  # Will be replaced by template
            template_name="email_template.html",
            template_vars={
                "subject": email_request.subject,
                "body": email_request.body
            }
        )
        
        if result["success"]:
            return EmailResponse(success=True, message=result["message"])
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except Exception as e:
        logger.error(f"Error in send_email endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/trigger-report/")
async def trigger_manual_report() -> Dict[str, Any]:
    """
    Manually trigger the daily email report.
    Useful for testing and debugging.
    """
    try:
        logger.info("Manual report trigger requested")
        await daily_email_report()
        return {
            "success": True,
            "message": "Report generation triggered successfully"
        }
    except Exception as e:
        logger.error(f"Error triggering manual report: {e}")
        raise HTTPException(status_code=500, detail=f"Error triggering report: {str(e)}")

async def daily_email_report():
    """
    Scheduled function to fetch emails, summarize them, and send a report.
    This runs every 24 hours automatically.
    """
    try:
        logger.info("Starting daily email report generation...")
        
        # Fetch recent emails from Gmail
        logger.info("Fetching emails from Gmail...")
        emails = gmail_fetcher.fetch_recent_emails(hours=24)
        
        if not emails:
            logger.info("No emails found in the last 24 hours")
            # Still send a report indicating no emails
            summaries = []
        else:
            logger.info(f"Found {len(emails)} emails, starting summarization...")
            # Summarize emails using LLM
            summaries = email_summarizer.summarize_emails_batch(emails)
        
        # Prepare report data
        report_data = {
            "date": datetime.utcnow().strftime("%B %d, %Y"),
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "total_emails": len(emails),
            "summaries": summaries
        }
        
        # Send report email
        report_recipient = os.getenv('REPORT_RECIPIENT_EMAIL')
        if not report_recipient:
            logger.error("REPORT_RECIPIENT_EMAIL not configured")
            return
        
        logger.info(f"Sending report to {report_recipient}")
        result = email_sender.send_html_report(report_recipient, report_data)
        
        if result["success"]:
            logger.info("Daily email report sent successfully")
        else:
            logger.error(f"Failed to send daily report: {result['message']}")
            
    except Exception as e:
        logger.error(f"Error in daily_email_report: {e}")

if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )