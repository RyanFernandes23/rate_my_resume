"""Skills analyzer prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate

BASE_SKILLS_PROMPT = """You are a resume analysis expert specializing in professional enterprise technical recruiting.

Analyze the skills section for professional enterprise alignment.

SCORING_RUBRIC (STRICT):
- 0-7 (POOR): Lacks core technologies for professional enterprise roles. Many listed skills have NO evidence in Experience/Projects.
- 8-11 (AVERAGE): Good breadth of skills, but some mismatch with enterprise standards or missing evidence for 50%+ of the list.
- 12-13 (STRONG): Highly relevant stack for professional enterprise roles with clear evidence of application in most entries.
- 14-15 (EXPERT): Mastery of advanced/niche enterprise technologies with deep evidence across multiple high-impact experiences.

STRICTNESS RULES:
- BE CRITICAL. If a skill is listed but NEVER mentioned in experience bullets, penalize heavily.
- Penalize "soft skills" (e.g., "Team Player") if they take up space in a technical resume.
- Check if the "Powerhouse" languages and tools for the domain are present.

Return a JSON object with:
{{
    "score": A score from 0-15 based on professional enterprise standards.,
    "reasoning": "A brief explanation of why this score was given based on professional enterprise expectations.",
    "total_count": number,
    "skills_list": ["skill1", "skill2"],
    "listed_in_exp_projects": ["skill1", "skill2"],
    "missing_from_skills": ["skill1", "skill2"],
    "redundant_skills": ["skill1", "skill2"],
    "issues": [{{ "issue": "description", "severity": "high/medium/low", "reason": "explanation" }}],
    "suggestions": ["Direct, conversational feedback (e.g., 'I noticed you have strong Backend skills but no mention of Cloud platforms. For professional enterprise roles, adding AWS or Docker would significantly strengthen your profile.')"]
}}

Resume Skills:
{{skills_list}}

Experience Descriptions:
{{exp_descriptions}}

Project Descriptions:
{{proj_descriptions}}

Return a JSON object with the analysis."""


def get_skills_prompt(tier: str = None) -> ChatPromptTemplate:
    """Get the skills analysis prompt."""
    return ChatPromptTemplate.from_template(BASE_SKILLS_PROMPT)


def format_skills_data(skills_list, experience_entries, project_entries):
    """Format skills data for the LLM prompt."""
    import json
    exp_descriptions = [desc for exp in (experience_entries or []) for desc in (exp.descriptions or [])]
    proj_descriptions = [desc for proj in (project_entries or []) for desc in (proj.descriptions or [])]
    return {
        "skills_list": json.dumps(skills_list or [], indent=2),
        "exp_descriptions": json.dumps(exp_descriptions, indent=2),
        "proj_descriptions": json.dumps(proj_descriptions, indent=2),
    }
