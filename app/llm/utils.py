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

def llm_retry(func):
    """
    Decorator to apply proactive rate limiting and reactive retries.
    Retries only on rate limit errors, trusting the client for other transient issues.
    """
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
    def wrapper(*args, **kwargs):
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
            # We don't update _last_call_time on failure to allow immediate retry if tenacity decides to
            raise e
            
    return wrapper
