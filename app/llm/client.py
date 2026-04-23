import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

load_dotenv()

LLM_MODE = os.getenv("LLM_MODE", "groq").lower()

if LLM_MODE == "openrouter":
    llm = ChatOpenAI(
        model="inclusionai/ling-2.6-1t:free",
        temperature=0.6,
        max_retries=2,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )
else:
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.6, max_retries=2)
