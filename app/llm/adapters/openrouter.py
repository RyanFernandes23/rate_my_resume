import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from ..protocol import LLMClient

load_dotenv()


class OpenRouterAdapter:
    def __init__(self) -> None:
        self._llm = ChatOpenAI(
            model=os.getenv("OPENROUTER_MODEL", "inclusionai/ling-2.6-1t:free"),
            temperature=0.0,
            max_retries=3,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )

    async def ainvoke(self, prompt: str) -> str:
        response = await self._llm.ainvoke(prompt)
        return response.content
