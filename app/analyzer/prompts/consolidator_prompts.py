"""Consolidator prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate


BASE_CONSOLIDATOR_PROMPT = """You are a senior recruitment strategist. Your task is to provide a final assessment of the candidate based on their resume analysis results with high-standard enterprise expectations.

Analysis data includes section status (found/missing) and scores. Use this to identify real strengths and genuine gaps. Do NOT suggest adding a section if it already exists with a received score.

Create a final JSON output with:
1. Overall Summary - A direct, no-nonsense conversational 3-4 sentence assessment of the candidate's fit. BE HONEST and CRITICAL. If the resume is weak, say so directly.
2. Strengths - list of 3-5 key strengths valuable for professional enterprise roles.
3. Areas for Improvement - list of 3-5 key improvements needed to meet high professional standards.

STRICTNESS RULES:
- If the benchmark grade is C or lower, the summary MUST be highly critical.
- Do not use generic praise unless it is truly deserved.
- Emphasize the biggest gap found in the scores.

Analysis Data:
{analysis_summary}

Return a JSON object with:
{{
    "overall_summary": "...",
    "strengths": ["...", "..."],
    "areas_for_improvement": ["...", "..."]
}}"""


def get_consolidator_prompt() -> ChatPromptTemplate:
    """Get the consolidation prompt."""
    return ChatPromptTemplate.from_template(BASE_CONSOLIDATOR_PROMPT)


def format_consolidator_data(
    basic_info_score,
    experience_score,
    projects_score,
    skills_score,
    education_score,
    achievements_hobbies_score,
    certifications_score,
    job_role_suggestions,
    benchmark_grade,
    education_status="",
    certifications_status="",
    achievements_status="",
):
    """Format consolidation data for the LLM prompt."""
    import json
    summary_data = {
        "basic_info_score": basic_info_score,
        "experience_score": experience_score,
        "projects_score": projects_score,
        "skills_score": skills_score,
        "education": education_status,
        "certifications": certifications_status,
        "achievements_hobbies": achievements_status,
        "job_role_suggestions": [r.role for r in job_role_suggestions[:3]] if job_role_suggestions else [],
        "benchmark_grade": benchmark_grade,
    }
    return {"analysis_summary": json.dumps(summary_data, indent=2)}
