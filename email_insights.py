"""AI-powered extraction of actionable insights from individual emails."""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from email_insight_schema import EmailInsight
from groq_model_manager import GroqModelManager

logger = logging.getLogger(__name__)


class EmailInsightExtractor:
    """Extract structured executive-assistant insights from one email at a time."""

    def __init__(self) -> None:
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.model_manager: Optional[GroqModelManager] = None

        if not self.groq_key:
            logger.error("GROQ_API_KEY not found in environment variables.")
            return

        try:
            self.model_manager = GroqModelManager(self.groq_key)
            logger.info("Groq model manager initialized with approved email models.")
        except Exception as exc:
            logger.error("Failed to initialize Groq model manager: %s", exc)

    def _validate_response(self, response: Any) -> Dict[str, Any]:
        """Parse JSON, validate the complete contract, and return normalized data."""
        raw_output = (response.choices[0].message.content or "").strip()
        try:
            raw_result = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            raise ValueError("AI returned invalid JSON") from exc

        try:
            validated = EmailInsight.model_validate(raw_result)
        except Exception as exc:
            logger.error("AI response failed Pydantic validation: %s", exc)
            raise ValueError("AI response does not match the required email insight schema") from exc

        return validated.model_dump(mode="json")

    def extract_insights(
        self,
        email: Dict[str, Any],
        current_datetime: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze exactly one email using adaptive model fallback and strict validation."""
        if not self.model_manager:
            raise RuntimeError("Groq AI service is not available")

        email_id = email.get("id")
        thread_id = email.get("thread_id")
        sender = email.get("sender")
        subject = email.get("subject") or "No Subject"
        content = email.get("content", email.get("snippet", ""))
        reference_datetime = current_datetime or "Not provided"

        prompt = f"""
You are Executive AI, a personal executive assistant.
Analyze the following single email and identify information that can help the user understand, decide, remember, and act.

CURRENT DATE/TIME REFERENCE:
{reference_datetime}

Use this current date/time reference to resolve relative temporal expressions in the email such as "today", "tomorrow", "yesterday", "next Monday", "this Friday", "in two days", or "next week".
When a relative date/time can be reliably resolved, output the corresponding absolute date/time rather than null.
Preserve the timezone/offset represented by the supplied current date/time when producing reminder datetimes.
If the email does not provide enough information to determine an exact time, keep the time as null while still resolving the date when possible.

Return ONLY one valid JSON object. Do not include markdown, commentary, or code fences.

Required JSON structure:
{{
  "id": {json.dumps(email_id)},
  "thread_id": {json.dumps(thread_id)},
  "sender": {json.dumps(sender)},
  "subject": {json.dumps(subject)},
  "is_important": false,
  "summary": "",
  "events": [],
  "actions": [],
  "deadlines": [],
  "reminders": []
}}

Rules:
- Analyze only this email. Do not invent facts.
- "is_important" should be true when the email contains information that is materially important to the user's responsibilities, schedule, finances, commitments, travel, appointments, deadlines, or required action.
- "summary" must be concise and explain the main purpose and important points.
- "events" contains actual or clearly confirmed scheduled events. Each event must use this structure:
  {{"title":"", "date":"YYYY-MM-DD or null", "time":"HH:MM or null", "location":null, "description":""}}
- "actions" contains things the user is expected or strongly encouraged to do. Each action must use:
  {{"title":"", "description":"", "due_date":"YYYY-MM-DD or null"}}
- "deadlines" contains explicit deadlines or due dates. Each deadline must use:
  {{"title":"", "date":"YYYY-MM-DD or null", "description":""}}
- "reminders" contains useful reminder suggestions. Each reminder must use:
  {{"title":"", "datetime":"ISO-8601 datetime or null", "reason":""}}
- Use [] when a category has no relevant items.
- Use null when a value cannot be determined reliably.
- Do not turn vague suggestions into confirmed events or deadlines.
- Preserve the supplied Gmail id and thread_id exactly.
- Do not assume a reminder time unless the email gives one or a sensible reminder time can be derived from an explicit deadline/event and the current date/time reference.

Email sender: {sender}
Email subject: {subject}
Email content:
{content}
"""

        response = self.model_manager.create_completion(
            response_validator=self._validate_response,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise personal executive assistant that extracts structured actionable information from emails. Return valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_completion_tokens=1200,
            stream=False,
        )

        result = self._validate_response(response)

        # Always retain the original Gmail identifiers supplied by Android.
        result["id"] = email_id
        result["thread_id"] = thread_id
        result["sender"] = sender
        result["subject"] = subject

        # Validate once more after restoring trusted source identifiers.
        return EmailInsight.model_validate(result).model_dump(mode="json")

    def process_emails(
        self,
        emails: List[Dict[str, Any]],
        current_datetime: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Process an account's emails sequentially, one AI request per email."""
        results: List[Dict[str, Any]] = []

        for index, email in enumerate(emails, start=1):
            logger.info("Extracting insights for email %d/%d", index, len(emails))
            try:
                results.append(self.extract_insights(email, current_datetime))
            except Exception as exc:
                logger.error("Failed to process email %d: %s", index, exc)
                results.append({
                    "id": email.get("id"),
                    "thread_id": email.get("thread_id"),
                    "sender": email.get("sender"),
                    "subject": email.get("subject") or "No Subject",
                    "is_important": False,
                    "summary": "",
                    "events": [],
                    "actions": [],
                    "deadlines": [],
                    "reminders": [],
                    "error": "Unable to analyze this email",
                })

        return results

    def is_available(self) -> bool:
        """Return whether the Groq model manager is initialized."""
        return self.model_manager is not None


email_insight_extractor = EmailInsightExtractor()
