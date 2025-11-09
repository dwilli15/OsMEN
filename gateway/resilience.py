#!/usr/bin/env python3
"""
Resilience patterns for OsMEN Agent Gateway
Provides retry logic, exponential backoff, and error handling for LLM API calls
"""

import logging

import httpx
from tenacity import (after_log, before_sleep_log, retry, retry_if_exception,
                      retry_if_exception_type, stop_after_attempt,
                      wait_exponential)

logger = logging.getLogger(__name__)


def is_retryable_http_error(exception):
    """Determine if an HTTP error should trigger a retry"""
    if isinstance(exception, httpx.HTTPStatusError):
        # Retry on server errors (5xx) and rate limiting (429)
        return exception.response.status_code in [429, 500, 502, 503, 504]
    return False


def retryable_llm_call(max_attempts=3, min_wait=2, max_wait=10):
    """
    Decorator for LLM API calls with retry logic
    
    Features:
    - Exponential backoff with jitter
    - Retries on transient errors (network, timeout, 5xx, 429)
    - Logs retry attempts
    - Configurable retry limits
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        min_wait: Minimum wait time in seconds (default: 2)
        max_wait: Maximum wait time in seconds (default: 10)
    
    Example:
        @retryable_llm_call(max_attempts=3)
        async def _openai_completion(self, request):
            response = await self.client.post(...)
            response.raise_for_status()
            return response
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=(
            retry_if_exception_type((
                httpx.TimeoutException,
                httpx.NetworkError,
                httpx.ConnectError,
                httpx.RemoteProtocolError
            )) | 
            retry_if_exception(is_retryable_http_error)
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.DEBUG),
        reraise=True
    )


def retryable_subprocess_call(max_attempts=2, min_wait=1, max_wait=5):
    """
    Decorator for subprocess calls (e.g., gh copilot, codex CLI)
    
    Less aggressive retry settings since subprocess failures are often not transient
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 2)
        min_wait: Minimum wait time in seconds (default: 1)
        max_wait: Maximum wait time in seconds (default: 5)
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type((
            TimeoutError,
            ConnectionError
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
