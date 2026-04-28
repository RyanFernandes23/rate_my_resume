"""Education analyzer using LangChain and externalized prompts."""
import json
from typing import Optional
from ..llm.client import llm
from ..analyzer.schemas import EducationAnalysis, GpaAnalysis, AnalysisIssue
from .prompts.education_prompts import get_education_prompt, format_education_data


def analyze_education(resume, tier="STANDARD"):
    """Analyze all education entries using LLM with externalized prompts."""
    from ..analyzer.schemas import EducationAnalysis

    if not resume.education:
        return []

    # Calculate total years of experience for context
    total_years_experience = 0
    if resume.experience:
        for exp in resume.experience:
            if exp.start_date:
                try:
                    from datetime import datetime
                    start = datetime.strptime(exp.start_date, "%Y-%m")
                    end = datetime.now()
                    if exp.end_date:
                        end = datetime.strptime(exp.end_date, "%Y-%m")
                    months = (end.year - start.year) * 12 + end.month - start.month
                    total_years_experience += months / 12
                except:
                    pass

    # Use LangChain prompt template
    prompt = get_education_prompt(tier)
    formatted_prompt = prompt.format(
        total_years=total_years_experience,
        education_data=format_education_data(resume.education),
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

        analyses = json.loads(json_str)

        result = []
        for analysis in analyses:
            idx = analysis.get("entry_index", 0)
            edu = resume.education[idx] if idx < len(resume.education) else None
            gpa_data = analysis.get("gpa_analysis", {})

            result.append(
                EducationAnalysis(
                    entry_index=idx,
                    institution_name_valid=analysis.get("institution_name_valid", True),
                    institution_name=analysis.get("institution_name", ""),
                    start_date=edu.start_date if edu else None,
                    end_date=edu.end_date if edu else None,
                    location=edu.location if edu else None,
                    date_issues=analysis.get("date_issues", []),
                    gpa_analysis=GpaAnalysis(
                        value=gpa_data.get("value") or (edu.score if edu else None),
                        recommendation=gpa_data.get("recommendation", "keep"),
                        reasoning=gpa_data.get("reasoning", ""),
                    ),
                    issues=[AnalysisIssue(**i) if isinstance(i, dict) else i for i in analysis.get("issues", [])],
                    suggestions=analysis.get("suggestions", [])[:1],
                    score=float(analysis.get("score", 8.0)),
                )
            )

        return result

    except Exception as e:
        print(f"Education analysis fallback triggered: {e}")
        return _fallback_education_analysis(resume, total_years_experience, e)


def _fallback_education_analysis(resume, total_years_experience, error):
    """Fallback analysis when LLM fails - simplified."""
    result = []
    for i, edu in enumerate(resume.education):
        score = 0.0
        if edu.name: score += 4.0
        if edu.start_date and edu.end_date: score += 3.0
        if edu.score: score += 3.0

        suggestion = "Keep it concise" if total_years_experience >= 2 else "Highlight academic achievements"

        result.append(
            EducationAnalysis(
                entry_index=i,
                institution_name_valid=bool(edu.name),
                institution_name=edu.name or "Education",
                start_date=edu.start_date,
                end_date=edu.end_date,
                location=edu.location,
                date_issues=[],
                gpa_analysis=GpaAnalysis(
                    value=edu.score,
                    recommendation="keep" if edu.score else "remove",
                    reasoning="Fallback assessment",
                ),
                issues=[AnalysisIssue(issue="Analyzer fallback", severity="low", reason=str(error))],
                suggestions=[suggestion],
                score=score,
            )
        )
    return result
