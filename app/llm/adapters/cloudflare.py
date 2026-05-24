import os
from langchain_cloudflare import ChatCloudflareWorkersAI
from dotenv import load_dotenv
from ..protocol import LLMClient

load_dotenv()


class CloudflareAdapter:
    def __init__(self, model: str = None) -> None:
        model = model or os.getenv("CLOUDFLARE_MODEL", "@cf/meta/llama-3.3-70b-instruct-fp8-fast")
        self._llm = ChatCloudflareWorkersAI(
            account_id=os.getenv("CLOUDFLARE_ACCOUNT_ID"),
            api_token=os.getenv("CLOUDFLARE_API_TOKEN"),
            model=model,
            max_tokens=4096,
        )

    async def ainvoke(self, prompt: str) -> str:
        response = await self._llm.ainvoke(prompt)
        return response.content
