"""Skills analyzer using LangChain and externalized prompts."""
import json
from ..llm.client import llm
from ..analyzer.schemas import SkillsAnalysis, AnalysisIssue
from .prompts.skills_prompts import get_skills_prompt, format_skills_data


def analyze_skills(resume):
    """Analyze skills with cross-reference to experience and projects using externalized prompts."""
    skills_list = resume.skills or []
    total_count = len(skills_list)

    # Use LangChain prompt template
    prompt = get_skills_prompt()
    formatted_data = format_skills_data(skills_list, resume.experience, resume.projects)
    formatted_prompt = prompt.format(
        skills_list=formatted_data["skills_list"],
        exp_descriptions=formatted_data["exp_descriptions"],
        proj_descriptions=formatted_data["proj_descriptions"],
    )

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

        analysis = json.loads(json_str)

        return SkillsAnalysis(
            total_count=total_count,
            skills_list=skills_list,
            listed_in_exp_projects=analysis.get("listed_in_exp_projects", []),
            missing_from_skills=analysis.get("missing_from_skills", []),
            redundant_skills=analysis.get("redundant_skills", []),
            issues=[AnalysisIssue(**i) if isinstance(i, dict) else i for i in analysis.get("issues", [])],
            suggestions=analysis.get("suggestions", [])[:3],
            score=max(0, float(analysis.get("score", 12.0))),
        )

    except Exception as e:
        print(f"Skills analysis fallback triggered: {e}")
        # Default fallback
        return SkillsAnalysis(
            total_count=total_count,
            skills_list=skills_list,
            listed_in_exp_projects=[],
            missing_from_skills=[],
            redundant_skills=[],
            issues=[AnalysisIssue(issue="Analyzer fallback", severity="low", reason=str(e))] if total_count > 0 else [AnalysisIssue(issue="No skills", severity="high", reason="Empty section")],
            suggestions=["Add a clear skills section"] if total_count == 0 else [],
            score=10.0 if total_count > 0 else 5.0,
        )
