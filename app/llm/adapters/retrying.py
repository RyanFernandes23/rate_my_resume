import time
import asyncio
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from ..protocol import LLMClient
from ..utils import is_rate_limit_error

logger = logging.getLogger(__name__)


class RetryingLLMClient:
    def __init__(self, inner: LLMClient, rate_limit_seconds: float = 0.5) -> None:
        self._inner = inner
        self._rate_limit_seconds = rate_limit_seconds
        self._last_call_time: float = 0

    async def ainvoke(self, prompt: str) -> str:
        await self._rate_limit()
        return await self._invoke_with_retry(prompt)

    async def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_call_time
        if elapsed < self._rate_limit_seconds:
            await asyncio.sleep(self._rate_limit_seconds - elapsed)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(is_rate_limit_error),
        reraise=True,
        before_sleep=lambda rs: logger.warning(
            f"Rate limited. Retrying attempt {rs.attempt_number} "
            f"after {rs.next_action.sleep}s..."
        ),
    )
    async def _invoke_with_retry(self, prompt: str) -> str:
        result = await self._inner.ainvoke(prompt)
        self._last_call_time = time.time()
        return result
