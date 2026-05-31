"""Standalone JD analyzer — runs as a separate parallel task, not bundled with skills/roles."""
import logging
import traceback
from typing import Optional
from ..llm.protocol import LLMClient
from ..llm.utils import parse_llm_json
from ..analyzer.schemas import JDAnalysis
from .prompts.jd_matcher_prompts import get_jd_matcher_prompt, format_jd_data

logger = logging.getLogger(__name__)


async def analyze_jd(resume, jd: Optional[str], llm_client: LLMClient, target_tier: str = "fresher") -> Optional[JDAnalysis]:
    """Analyze resume against a job description in a dedicated LLM call."""
    if not jd:
        return None

    try:
        prompt = get_jd_matcher_prompt(tier=target_tier)
        data = format_jd_data(jd, resume)
        formatted = prompt.format(**data)
        response = await llm_client.ainvoke(formatted)
        result = parse_llm_json(response)
        return JDAnalysis(
            match_score=result.get("match_score", 0.0),
            compatible_roles=result.get("compatible_roles", []),
            missing_critical_skills=result.get("missing_critical_skills", []),
            missing_nice_to_have=result.get("missing_nice_to_have", []),
            tailoring_recommendations=result.get("tailoring_recommendations", []),
        )
    except Exception as e:
        logger.error("JD analysis failed:\n%s", traceback.format_exc())
        return None
