from typing import Protocol


class LLMClient(Protocol):
    async def ainvoke(self, prompt: str) -> str:
        ...
