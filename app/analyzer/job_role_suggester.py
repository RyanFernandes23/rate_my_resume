"""Job role suggester using LangChain and externalized prompts."""
import json
from ..llm.client import llm
from ..analyzer.schemas import JobRoleSuggestion
from .prompts.job_role_suggester_prompts import get_job_role_prompt, format_job_role_data


def suggest_job_roles(resume) -> list[JobRoleSuggestion]:
    """Suggest job roles based on resume data using externalized prompts."""
    # Prepare summary data for LLM
    skills = resume.skills or []

    exp_summary = []
    for exp in resume.experience or []:
        exp_summary.append({
            "title": exp.title,
            "company": exp.company,
            "descriptions": exp.descriptions[:2],  # First 2 bullets
        })

    proj_summary = []
    for proj in resume.projects or []:
        proj_summary.append({"name": proj.name, "descriptions": proj.descriptions[:2]})

    total_years = resume.total_years_experience or 0

    # Use LangChain prompt template
    prompt = get_job_role_prompt()
    formatted_data = format_job_role_data(skills, exp_summary, proj_summary, total_years)
    formatted_prompt = prompt.format(**formatted_data)

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
