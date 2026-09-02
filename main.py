"""
FastAPI Email Automation App
Main application with API endpoints and scheduled tasks.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

from mail_utils.sender import gmail_manager
from email_utils import email_sender
from gmail_utils import gmail_fetcher
from summarizer import email_summarizer
from email_insights import email_insight_extractor

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


class EmailRequest(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str


class EmailResponse(BaseModel):
    success: bool
    message: str


class EmailInsightInput(BaseModel):
    id: str
    thread_id: Optional[str] = None
    sender: Optional[str] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    snippet: Optional[str] = None


class ExtractInsightsRequest(BaseModel):
    emails: List[EmailInsightInput]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Email Manager application...")
    scheduler.start()
    scheduler.add_job(
        func=daily_email_report_for_multiple_recipients,
        trigger="interval",
        hours=24,
        id="daily_email_report",
        replace_existing=True
    )
    logger.info("Scheduler started - daily email reports will run every 24 hours")

    if os.getenv('DEBUG') == 'True':
        scheduler.add_job(
            func=daily_email_report_for_multiple_recipients,
            trigger="date",
            run_date=datetime.now() + timedelta(seconds=10),
            id="initial_report",
            max_instances=1
        )

    yield
    logger.info("Shutting down Email Manager application...")
    scheduler.shutdown()


app = FastAPI(
    title="Email Manager API",
    description="FastAPI Email Automation App with Gmail fetching and LLM summarization",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
async def root() -> Dict[str, Any]:
    return {
        "message": "Email Manager API",
        "version": "1.0.0",
        "endpoints": {
            "send_email": "/send-email/",
            "extract_insights_from_emails": "/extract-insights-from-emails/",
            "health": "/health",
            "status": "/status"
        }
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "email_sender": bool(email_sender.email_address and email_sender.email_password),
            "summarizer": email_summarizer.is_available(),
            "email_insights": email_insight_extractor.is_available()
        }
    }


@app.get("/status")
async def get_status() -> Dict[str, Any]:
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
        "llm_available": email_summarizer.is_available(),
        "email_insights_available": email_insight_extractor.is_available()
    }


@app.post("/extract-insights-from-emails/")
async def extract_insights_from_emails(request: ExtractInsightsRequest) -> Dict[str, Any]:
    """Receive one account's emails and send them to the AI one at a time."""
    if not email_insight_extractor.is_available():
        raise HTTPException(status_code=503, detail="AI service is not available")

    if not request.emails:
        return {"emails": []}

    emails = [email.model_dump() for email in request.emails]
    logger.info("Received %d emails for sequential insight extraction", len(emails))

    results = email_insight_extractor.process_emails(emails)
    return {"emails": results}


@app.post("/send-email/", response_model=EmailResponse)
async def send_email(email_request: EmailRequest) -> EmailResponse:
    try:
        logger.info(f"Received email from {email_request.email}")
        result = email_sender.send_email(
            to_email="inimfonebong001@gmail.com",
            subject=email_request.subject,
            body="",
            template_name="email_template.html",
            template_vars={
                "subject": email_request.subject,
                "message": email_request.message,
                "email": email_request.email,
                "name": email_request.name,
            }
        )
        if result["success"]:
            return EmailResponse(success=True, message=result["message"])
        raise HTTPException(status_code=500, detail=result["message"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send_email endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/trigger-report/")
async def trigger_manual_report() -> Dict[str, Any]:
    try:
        logger.info("Manual report trigger requested")
        await daily_email_report_for_multiple_recipients()
        return {"success": True, "message": "Report generation triggered successfully"}
    except Exception as e:
        logger.error(f"Error triggering manual report: {e}")
        raise HTTPException(status_code=500, detail=f"Error triggering report: {str(e)}")


async def daily_email_report(recipient_email: str, email_password: str):
    try:
        logger.info(f"Starting daily email report generation for {recipient_email}...")
        email_sender.set_credentials(recipient_email, email_password)
        gmail_manager.set_credentials(recipient_email, email_password)
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


async def daily_email_report_for_multiple_recipients():
    recipients = ["inimfonebong001@gmail.com", "ebonginimfon8@gmail.com"]
    for recipient in recipients:
        username = recipient.split("@")[0].upper()
        password = os.getenv(f"{username}_PASSWORD")
        if not password:
            logger.error(f"No password found for {recipient} (env var: {username}_PASSWORD). Skipping.")
            continue
        await daily_email_report(recipient, password)


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=debug, log_level="info")
