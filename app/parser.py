import time
import logging

from langchain_openrouter import ChatOpenRouter
from langchain_core.messages import HumanMessage

from app import config
from app.models import ResumeDocument
from app.logger import log_api_call

logger = logging.getLogger("rate_my_resume")

PRIMARY_MODEL = "google/gemma-3-27b-it:free"
FALLBACK_MODEL = "openrouter/free"


class ResumeParser:
    def __init__(self, model_name: str = PRIMARY_MODEL):
        self.model_name = model_name
        self.last_model_used = None

    def _create_llm(self, model_name: str) -> ChatOpenRouter:
        return ChatOpenRouter(
            model=model_name,
            temperature=0.1,
            max_completion_tokens=4000,
        )

    def parse(self, text_content: str) -> ResumeDocument:
        start_time = time.time()

        for model_name in [PRIMARY_MODEL, FALLBACK_MODEL]:
            try:
                logger.info(f"Attempting parse with structured output: {model_name}")

                llm = self._create_llm(model_name)
                structured_llm = llm.with_structured_output(ResumeDocument)

                result = structured_llm.invoke(text_content)

                self.last_model_used = model_name
                duration = int((time.time() - start_time) * 1000)
                log_api_call("parse_resume", "success", duration, model_name)
                logger.info(f"Parse succeeded with {model_name} in {duration}ms")

                return result

            except Exception as e:
                error_str = str(e).lower()
                duration = int((time.time() - start_time) * 1000)

                if "no endpoints" in error_str or "tool" in error_str:
                    logger.warning(
                        f"Structured output not supported with {model_name}, trying next..."
                    )
                    continue
                elif "rate limit" in error_str:
                    logger.warning(f"Rate limit with {model_name}, trying next...")
                    continue
                else:
                    logger.warning(f"Parse failed with {model_name}: {str(e)[:100]}")
                    continue

        total_duration = int((time.time() - start_time) * 1000)
        error_msg = f"All models failed for structured output parsing"
        log_api_call("parse_resume", "error", total_duration, "all", error=error_msg)
        logger.error(error_msg)
        raise Exception(error_msg)
