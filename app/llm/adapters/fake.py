from collections.abc import Callable
from ..protocol import LLMClient


class FakeLLMClient:
    def __init__(self, handler: Callable[[str], str] | None = None):
        self._handler = handler or (lambda _: "")
        self.calls: list[str] = []

    async def ainvoke(self, prompt: str) -> str:
        self.calls.append(prompt)
        return self._handler(prompt)
