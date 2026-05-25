"""Utility functions for resume analysis transformation."""
from app.analyzer.schemas import ResumeAnalysis
from app.llm.schema import Resume
from typing import Optional


def transform_to_frontend_format(
    analysis: ResumeAnalysis, resume: Resume = None, page_count: int = 1
) -> dict:
    """Transform analyzer output to match frontend expected format"""

    sb = analysis.score_breakdown

    validation_errors = []
    if analysis.basic_info_analysis:
        if not analysis.basic_info_analysis.name.is_valid:
            validation_errors.append("Name is missing or invalid")
        if not analysis.basic_info_analysis.email.is_valid:
            validation_errors.append("Email is missing or invalid")
        if not analysis.basic_info_analysis.phone.is_valid:
            validation_errors.append("Phone is missing or invalid")

    if not analysis.skills_analysis or analysis.skills_analysis.total_count == 0:
        validation_errors.append("No skills found")

    bi = analysis.basic_info_analysis
    bi_suggestions = []
    if bi:
        bi_suggestions.extend(bi.name.suggestions or [])
        bi_suggestions.extend(bi.email.suggestions or [])
        bi_suggestions.extend(bi.phone.suggestions or [])
        bi_suggestions.extend(bi.links.suggestions or [])

    sections = [
        {"name": "Basic Information", "score": sb.basic_info_score, "max_score": 10, "suggestions": list(dict.fromkeys(bi_suggestions))},
        {"name": "Experience", "score": sb.experience_score, "max_score": 25, "suggestions": []},
        {"name": "Projects", "score": sb.projects_score, "max_score": 25, "suggestions": []},
        {"name": "Skills", "score": sb.skills_score, "max_score": 15, "suggestions": analysis.skills_analysis.suggestions if analysis.skills_analysis else []},
        {"name": "Education", "score": sb.education_score, "max_score": 10, "suggestions": list(dict.fromkeys([s for edu in (analysis.education_analysis or []) for s in edu.suggestions]))},
        {"name": "Achievements", "score": sb.achievements_score, "max_score": 10, "suggestions": analysis.achievements_analysis.suggestions if analysis.achievements_analysis else []},
        {"name": "Certifications", "score": sb.certifications_score, "max_score": 5, "suggestions": list(dict.fromkeys([s for cert in (analysis.certifications_analysis or []) for s in cert.suggestions]))},
    ]

    return {
        "total_score": sb.total_score,
        "total_percentage": sb.converted_percentage,
        "score_breakdown": {
            "basic_info_score": sb.basic_info_score,
            "experience_score": sb.experience_score,
            "projects_score": sb.projects_score,
            "skills_score": sb.skills_score,
            "education_score": sb.education_score,
             "achievements_score": sb.achievements_score,
            "certifications_score": sb.certifications_score,
            "job_role_fit_score": sb.job_role_fit_score,
            "total_score": sb.total_score,
            "total_percentage": sb.total_percentage,
            "converted_percentage": sb.converted_percentage,
            "benchmark_grade": sb.benchmark_grade,
            "target_tier": sb.target_tier,
        },
        "is_valid": len(validation_errors) == 0,
        "validation_errors": validation_errors,
        "strengths": analysis.strengths,
        "areas_for_improvement": analysis.areas_for_improvement,
        "sections": sections,
        "experience_analysis": [{"entry_summary": exp.entry_summary, "star_score": exp.star_principle_score, "impact_score": exp.impact_score, "recommendation": exp.recommendation, "suggestions": [{"bullet_index": s.bullet_index, "original_bullet": s.original_bullet, "context": s.context, "advice": s.advice, "rewrites": s.rewrites} for s in exp.suggestions], "good_things": exp.good_things, "score": exp.score} for exp in (analysis.experience_analysis or [])],
        "projects_analysis": [{"entry_name": proj.entry_name, "star_score": proj.star_principle_score, "impact_score": proj.impact_score, "recommendation": proj.recommendation, "suggestions": [{"bullet_index": s.bullet_index, "original_bullet": s.original_bullet, "context": s.context, "advice": s.advice, "rewrites": s.rewrites} for s in proj.suggestions], "good_things": proj.good_things, "score": proj.score} for proj in (analysis.projects_analysis or [])],
        "job_role_suggestions": [{"role": role.role, "match_score": role.match_score, "reasoning": role.reasoning, "suggestions": role.suggestions} for role in (analysis.job_role_suggestions or [])],
        "benchmark_grade": sb.benchmark_grade,
        "target_tier": sb.target_tier,
        "jd_analysis": {"match_score": analysis.jd_analysis.match_score, "compatible_roles": analysis.jd_analysis.compatible_roles, "missing_critical_skills": analysis.jd_analysis.missing_critical_skills, "missing_nice_to_have": analysis.jd_analysis.missing_nice_to_have, "tailoring_recommendations": analysis.jd_analysis.tailoring_recommendations} if analysis.jd_analysis else None,
    }
