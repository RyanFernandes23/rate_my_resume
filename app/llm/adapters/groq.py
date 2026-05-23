import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from ..protocol import LLMClient

load_dotenv()


class GroqAdapter:
    def __init__(self) -> None:
        self._llm = ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            temperature=0.2,
            max_retries=3,
        )

    async def ainvoke(self, prompt: str) -> str:
        response = await self._llm.ainvoke(prompt)
        return response.content
