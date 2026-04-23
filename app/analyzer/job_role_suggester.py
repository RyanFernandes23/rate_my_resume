import json
from ..llm.client import llm
from .schemas import JobRoleSuggestion


JOB_ROLE_PROMPT = """You are a career advisor and resume analysis expert.

Based on the resume data (skills, experience, projects), suggest suitable job roles.

Analysis Criteria:
1. Match skills to job roles (technical skills, soft skills)
2. Consider experience level and type
3. Look at project technologies for specialization
4. Factor in total years of experience

For each suggested role, return a JSON object with:
{
    "role": "Job Role Title",
    "match_score": number (0-10),
    "reasoning": "Why this role fits based on skills/experience",
    "suggestions": ["How to tailor resume for this role"]
}

Requirements:
- Suggest minimum 5 job roles
- Include both entry-level and senior roles if applicable
- Consider popular tech roles: Software Engineer, Data Scientist, ML Engineer, DevOps, Full Stack, etc.
- Provide match score based on how well resume fits the role
- Reasoning should reference specific skills/experience from resume

Return a JSON array of at least 5 job role suggestions sorted by match score (highest first)."""


def suggest_job_roles(resume) -> list[JobRoleSuggestion]:
    """Suggest job roles based on resume data"""

    # Prepare summary data for LLM
    skills = resume.skills or []

    exp_summary = []
    for exp in resume.experience or []:
        exp_summary.append(
            {
                "title": exp.title,
                "company": exp.company,
                "descriptions": exp.descriptions[:2],  # First 2 bullets
            }
        )

    proj_summary = []
    for proj in resume.projects or []:
        proj_summary.append({"name": proj.name, "descriptions": proj.descriptions[:2]})

    total_years = resume.total_years_experience or 0

    prompt = f"""{JOB_ROLE_PROMPT}

Resume Data:
Skills: {json.dumps(skills, indent=2)}

Experience ({total_years} years):
{json.dumps(exp_summary, indent=2)}

Projects:
{json.dumps(proj_summary, indent=2)}

Return a JSON array of at least 5 job role suggestions."""

    try:
        response = llm.invoke(prompt)
        json_str = response.content.strip()

        # Clean up markdown
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        elif json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()

        suggestions = json.loads(json_str)

        # Convert to JobRoleSuggestion objects
        result = []
        for s in suggestions:
            result.append(
                JobRoleSuggestion(
                    role=s.get("role", ""),
                    match_score=s.get("match_score", 5.0),
                    reasoning=s.get("reasoning", ""),
                    suggestions=s.get("suggestions", []),
                )
            )

        return result

    except Exception as e:
        # Fallback - return generic suggestions
        return [
            JobRoleSuggestion(
                role="Software Engineer",
                match_score=7.0,
                reasoning="Based on programming skills and projects",
                suggestions=["Add more technical details to experience"],
            ),
            JobRoleSuggestion(
                role="Full Stack Developer",
                match_score=6.5,
                reasoning="Skills in both frontend and backend technologies",
                suggestions=["Highlight full stack projects"],
            ),
            JobRoleSuggestion(
                role="Python Developer",
                match_score=6.5,
                reasoning="Strong Python skills mentioned",
                suggestions=["Showcase Python projects"],
            ),
            JobRoleSuggestion(
                role="Machine Learning Engineer",
                match_score=6.0,
                reasoning="PyTorch and ML projects present",
                suggestions=["Add more ML/DL projects"],
            ),
            JobRoleSuggestion(
                role="Data Analyst",
                match_score=5.5,
                reasoning="Analytics tools and skills present",
                suggestions=["Highlight analytical projects"],
            ),
        ]
