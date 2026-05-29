"""JD matcher prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate

BASE_JD_MATCHER_PROMPT = """You are a senior recruiter comparing a candidate's resume against a Job Description (JD).
Return ONLY valid JSON. No preamble, no explanation, no markdown code fences — just the raw JSON object.

Evaluate alignment across these dimensions:
1. Tech/Skills Alignment: Exact matches vs adjacent ones.
2. Experience Depth: Does the candidate meet the seniority level indicated by the JD?
3. Domain Knowledge: Match between candidate projects and JD domain.
4. Impact Match: Are the JD's core responsibilities reflected in the candidate's achievements?

CANDIDATE TIER GUIDANCE:
- Fresher (0-2 years): Evaluate for potential and foundational fit. Lower seniority is expected. Focus on adjacent skills and aptitude. Do not penalise heavily for missing senior-level requirements.
- Experienced (3+ years): Evaluate for deep domain expertise, proven impact, and leadership. Seniority mismatch is meaningful.

SCORING_RUBRIC:
- 0-30 (POOR): Major skills gap. Limited overlap with JD requirements.
- 31-60 (AVERAGE): Meets some requirements but lacks key skills or domain experience.
- 61-85 (STRONG): Meets most must-have requirements. Good alignment.
- 86-100 (EXPERT): Excellent match with strong domain overlap and impact evidence.

Return ONLY this JSON structure (no other text):
{{"match_score": 0-100, "compatible_roles": ["role1", "role2"], "missing_critical_skills": ["skill1"], "missing_nice_to_have": ["skill2"], "tailoring_recommendations": ["advice1", "advice2"]}}

JOB DESCRIPTION:
{jd}

RESUME SUMMARY:
Name: {name}
Skills: {skills}
Experience: {experience}
Professional Summary: {professional_summary}"""


def get_jd_matcher_prompt(tier: str = "fresher") -> ChatPromptTemplate:
    """Get the JD matching prompt with tier-aware context injected."""
    tier_context = "fresher" if tier == "fresher" else "experienced"
    prompt = BASE_JD_MATCHER_PROMPT.replace(
        "CANDIDATE TIER GUIDANCE:",
        f"CANDIDATE TIER: {tier_context.upper()}\nCANDIDATE TIER GUIDANCE:"
    )
    return ChatPromptTemplate.from_template(prompt)


def format_jd_data(jd, resume):
    """Format JD and resume data for the LLM prompt."""
    import json
    skills = resume.skills or []
    exp_titles = [f"{e.title} at {e.company}" for e in resume.experience or []]
    return {
        "jd": jd,
        "name": resume.name,
        "skills": json.dumps(skills),
        "experience": json.dumps(exp_titles),
        "professional_summary": resume.professional_summary or "None",
    }
