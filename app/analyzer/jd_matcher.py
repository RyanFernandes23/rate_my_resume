"""JD matcher using LangChain and externalized prompts."""
import json
from ..llm.client import llm
from ..analyzer.schemas import JDAnalysis
from .prompts.jd_matcher_prompts import get_jd_matcher_prompt, format_jd_data


def match_with_jd(resume, jd: str, tier: str = "STANDARD"):
    """Compare resume with a specific Job Description using externalized prompts."""
    if not jd:
        return None

    # Use LangChain prompt template
    prompt = get_jd_matcher_prompt(tier)
    formatted_prompt = prompt.format(**format_jd_data(jd, resume))

    try:
        response = llm.invoke(formatted_prompt)
        json_str = response.content.strip()

        # Clean up markdown
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        elif json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()

        data = json.loads(json_str)

        return JDAnalysis(
            match_score=data.get("match_score", 0.0),
            compatible_roles=data.get("compatible_roles", []),
            missing_critical_skills=data.get("missing_critical_skills", []),
            missing_nice_to_have=data.get("missing_nice_to_have", []),
            tailoring_recommendations=data.get("tailoring_recommendations", [])
        )

    except Exception as e:
        print(f"Error in JD matching: {e}")
        return None
