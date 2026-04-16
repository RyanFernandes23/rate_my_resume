import time
import threading
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)

MIN_DELAY_SECONDS = 4.0


class RateLimiter:
    _lock = threading.Lock()
    _last_call_time = 0.0
    _min_delay = MIN_DELAY_SECONDS

    @classmethod
    def wait_if_needed(cls) -> None:
        with cls._lock:
            now = time.time()
            time_since_last = now - cls._last_call_time
            if time_since_last < cls._min_delay:
                wait_time = cls._min_delay - time_since_last
                logger.debug(
                    f"Rate limit: waiting {wait_time:.2f}s before next request"
                )
                time.sleep(wait_time)
            cls._last_call_time = time.time()

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            cls._last_call_time = 0.0


def rate_limit_call(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        RateLimiter.wait_if_needed()
        logger.debug(f"Rate limit: executing {func.__name__}")
        return func(*args, **kwargs)

    return wrapper
