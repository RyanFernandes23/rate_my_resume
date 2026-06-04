import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from ..protocol import LLMClient

load_dotenv()


class GroqAdapter:
    def __init__(self, model: str = None) -> None:
        model = model or os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        self._llm = ChatGroq(
            model=model,
            temperature=0.1,
            max_retries=3,
            max_tokens=8192,
        )

    async def ainvoke(self, prompt: str) -> str:
        response = await self._llm.ainvoke(prompt)
        return response.content
