"""Job role suggester prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate

BASE_JOB_ROLE_PROMPT = """You are a senior career advisor specialized in professional enterprise recruiting.

Based on the resume data below, suggest suitable job roles specifically within the professional enterprise ecosystem.

For each suggested role, return a JSON object with:
{{
    "role": "Job Role Title",
    "match_score": number (0-10),
    "reasoning": "Why this role fits based on skills/experience within the professional enterprise context",
    "suggestions": ["How to tailor resume specifically for this professional enterprise role"]
}}

Resume Data:
Skills: {{skills}}

Experience ({{total_years}} years):
{{experience}}

Projects:
{{projects}}

Return a JSON array of at least 5 job role suggestions sorted by match score (highest first)."""


def get_job_role_prompt(tier: str = None) -> ChatPromptTemplate:
    """Get the job role suggestion prompt."""
    return ChatPromptTemplate.from_template(BASE_JOB_ROLE_PROMPT)


def format_job_role_data(skills, experience, projects, total_years):
    """Format job role data for the LLM prompt."""
    import json
    return {
        "skills": json.dumps(skills or [], indent=2),
        "experience": json.dumps(experience or [], indent=2),
        "projects": json.dumps(projects or [], indent=2),
        "total_years": total_years,
    }
