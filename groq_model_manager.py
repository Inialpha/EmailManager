"""Resilient model routing for Executive AI email insight extraction."""

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from groq import Groq

logger = logging.getLogger(__name__)


APPROVED_EMAIL_MODELS: List[str] = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b",
    "qwen/qwen3.8-27b",
]


class GroqModelManager:
    """Select and fail over between approved Groq models automatically."""

    def __init__(self, api_key: str, models: Optional[List[str]] = None, max_model_attempts: Optional[int] = None) -> None:
        self.models = list(models or APPROVED_EMAIL_MODELS)
        self.max_model_attempts = max_model_attempts or len(self.models)
        self.cooldowns: Dict[str, float] = {}
        # Disable SDK retries so a rate-limited model does not retry itself
        # before our fallback router can select another approved model.
        self.client = Groq(api_key=api_key, max_retries=0)

    @staticmethod
    def _retry_after_seconds(exc: Exception) -> Optional[float]:
        response = getattr(exc, "response", None)
        headers = getattr(response, "headers", None)
        if headers:
            value = headers.get("retry-after") or headers.get("Retry-After")
            if value:
                try:
                    return max(0.0, float(value))
                except (TypeError, ValueError):
                    pass
        return None

    @staticmethod
    def _status_code(exc: Exception) -> Optional[int]:
        value = getattr(exc, "status_code", None)
        if value is None:
            response = getattr(exc, "response", None)
            value = getattr(response, "status_code", None)
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    def _is_rate_limited(self, exc: Exception) -> bool:
        return self._status_code(exc) == 429 or "rate limit" in str(exc).lower()

    def _is_retryable(self, exc: Exception) -> bool:
        status = self._status_code(exc)
        return self._is_rate_limited(exc) or status in {408, 409, 500, 502, 503, 504}

    def _cooldown_model(self, model: str, seconds: float) -> None:
        self.cooldowns[model] = time.monotonic() + max(1.0, seconds + 1.0)
        logger.warning("Model %s cooling down for %.1f seconds", model, seconds)

    def _available_models(self) -> List[str]:
        now = time.monotonic()
        return [model for model in self.models if self.cooldowns.get(model, 0.0) <= now]

    def _wait_for_earliest_model(self) -> None:
        if not self.cooldowns:
            return
        delay = min(self.cooldowns.values()) - time.monotonic()
        if delay > 0:
            logger.info("All approved Groq models are cooling down; waiting %.1f seconds", delay)
            time.sleep(delay)

    def create_completion(self, response_validator: Optional[Callable[[Any], Any]] = None, **kwargs: Any) -> Any:
        """Create a completion and fail over across approved models.

        Rate limits, transient provider errors, and invalid model output all
        trigger the next approved model. Authentication/configuration errors
        are raised immediately because changing models cannot fix them.
        """
        attempted: List[str] = []
        last_error: Optional[Exception] = None

        for _ in range(self.max_model_attempts):
            available = self._available_models()
            if not available:
                self._wait_for_earliest_model()
                available = self._available_models()
            if not available:
                break

            model = next((m for m in available if m not in attempted), None)
            if model is None:
                break
            attempted.append(model)

            request_kwargs = dict(kwargs)
            request_kwargs["model"] = model
            logger.info("Trying Groq model %s", model)

            try:
                response = self.client.chat.completions.create(**request_kwargs)
            except Exception as exc:
                last_error = exc
                status = self._status_code(exc)

                if self._is_rate_limited(exc):
                    retry_after = self._retry_after_seconds(exc) or 5.0
                    self._cooldown_model(model, retry_after)
                    logger.warning("Groq model %s rate-limited (HTTP %s); switching model", model, status or 429)
                    continue

                if self._is_retryable(exc):
                    self._cooldown_model(model, 2.0)
                    logger.warning("Transient Groq error from model %s (HTTP %s); switching model: %s", model, status or "unknown", exc)
                    continue

                raise

            if response_validator is not None:
                try:
                    response_validator(response)
                except Exception as exc:
                    last_error = exc
                    self._cooldown_model(model, 1.0)
                    logger.warning("Groq model %s returned unusable output; switching model: %s", model, exc)
                    continue

            logger.info("Groq model %s succeeded", model)
            return response

        if last_error is not None:
            raise RuntimeError(f"All approved Groq models failed after trying: {', '.join(attempted)}") from last_error
        raise RuntimeError("No approved Groq model is currently available")


__all__ = ["APPROVED_EMAIL_MODELS", "GroqModelManager"]
