import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_cloudflare import ChatCloudflareWorkersAI
from .utils import llm_retry

load_dotenv()

LLM_MODE = os.getenv("LLM_MODE", "groq").lower()

if LLM_MODE == "openrouter":
    llm = ChatOpenAI(
        model=os.getenv("OPENROUTER_MODEL", "inclusionai/ling-2.6-1t:free"),
        temperature=0.0,
        max_retries=2,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )
elif LLM_MODE == "cloudflare":
    llm = ChatCloudflareWorkersAI(
        account_id=os.getenv("CLOUDFLARE_ACCOUNT_ID"),
        api_token=os.getenv("CLOUDFLARE_API_TOKEN"),
        model=os.getenv("CLOUDFLARE_MODEL", "@cf/meta/llama-3.3-70b-instruct-fp8-fast"),
        max_tokens=4096,
    )
else:
    llm = ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"), 
        temperature=0.2, 
        max_retries=2
    )

# Centralized decoration of the invoke method
# We use object.__setattr__ to bypass Pydantic's restriction on setting attributes
object.__setattr__(llm, 'invoke', llm_retry(llm.invoke))
object.__setattr__(llm, 'ainvoke', llm_retry(llm.ainvoke))
