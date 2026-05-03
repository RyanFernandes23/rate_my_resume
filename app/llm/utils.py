import time
import functools
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

logger = logging.getLogger(__name__)

# Track last call globally for proactive rate limiting
_last_call_time = 0
RATE_LIMIT_SECONDS = 0.5  # Adjust as needed for the specific LLM tier

def is_rate_limit_error(e: Exception) -> bool:
    """Check if an exception is a rate limit error."""
    error_str = str(e).lower()
    error_type = type(e).__name__.lower()
    return (
        "toomanyrequests" in error_str
        or "toomanyrequests" in error_type
        or "429" in error_str
        or "rate limit" in error_str
    )

import json
import re

def parse_llm_json(content: str):
    """Extract and parse JSON from LLM response content."""
    json_str = content.strip()

    # Try to find JSON if there's preamble/postamble
    # Search for first { or [ and last } or ]
    start_brace = json_str.find("{")
    start_bracket = json_str.find("[")
    
    start_idx = -1
    if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket):
        start_idx = start_brace
        end_idx = json_str.rfind("}")
    elif start_bracket != -1:
        start_idx = start_bracket
        end_idx = json_str.rfind("]")
        
    if start_idx != -1 and end_idx != -1:
        json_str = json_str[start_idx:end_idx+1]

    if json_str.startswith("```json"):
        json_str = json_str[7:]
    elif json_str.startswith("```"):
        json_str = json_str[3:]
    if json_str.endswith("```"):
        json_str = json_str[:-3]
    json_str = json_str.strip()
    
    if not json_str:
        raise ValueError("Empty JSON string extracted from LLM response")

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # Common LLM mistake: single quotes instead of double quotes
        # We try a simple regex fix if it looks like a dictionary with single quotes
        if "'" in json_str and '"' not in json_str:
            try:
                # This is a bit risky but often works for simple LLM outputs
                fixed_str = json_str.replace("'", '"')
                return json.loads(fixed_str)
            except:
                pass
        raise e

import asyncio

def llm_retry(func):
    """
    Decorator to apply proactive rate limiting and reactive retries.
    Supports both sync and async functions.
    """
    if asyncio.iscoroutinefunction(func):
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception(is_rate_limit_error),
            reraise=True,
            before_sleep=lambda retry_state: logger.warning(
                f"Rate limited by provider. Retrying attempt {retry_state.attempt_number} after {retry_state.next_action.sleep}s..."
            )
        )
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            global _last_call_time
            
            # Proactive rate limiting
            elapsed = time.time() - _last_call_time
            if elapsed < RATE_LIMIT_SECONDS:
                await asyncio.sleep(RATE_LIMIT_SECONDS - elapsed)
            
            try:
                result = await func(*args, **kwargs)
                _last_call_time = time.time()
                return result
            except Exception as e:
                raise e
        return async_wrapper
    else:
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception(is_rate_limit_error),
            reraise=True,
            before_sleep=lambda retry_state: logger.warning(
                f"Rate limited by provider. Retrying attempt {retry_state.attempt_number} after {retry_state.next_action.sleep}s..."
            )
        )
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            global _last_call_time
            
            # Proactive rate limiting
            elapsed = time.time() - _last_call_time
            if elapsed < RATE_LIMIT_SECONDS:
                time.sleep(RATE_LIMIT_SECONDS - elapsed)
            
            try:
                result = func(*args, **kwargs)
                _last_call_time = time.time()
                return result
            except Exception as e:
                raise e
        return sync_wrapper
