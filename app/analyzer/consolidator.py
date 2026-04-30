"""Consolidator using LangChain and externalized prompts."""
import json
from ..llm.client import llm
from ..analyzer.schemas import ScoreBreakdown, ResumeAnalysis
from .prompts.consolidator_prompts import get_consolidator_prompt, format_consolidator_data


def consolidate_analysis(
    basic_info_analysis,
    experience_analysis,
    projects_analysis,
    skills_analysis,
    education_analysis,
    achievements_hobbies_analysis,
    certifications_analysis,
    job_role_suggestions
):
    """Consolidate all analyses and calculate final scores."""

    # Calculate section scores
    # Basic Info Score (out of 10)
    if basic_info_analysis:
        bi_score = 10.0
        if not basic_info_analysis.name.is_valid:
            bi_score -= 2
        if not basic_info_analysis.email.is_valid:
            bi_score -= 2
        if not basic_info_analysis.phone.is_valid:
            bi_score -= 2
        if not basic_info_analysis.links.is_valid:
            bi_score -= 2
        basic_info_score = max(0, bi_score)
    else:
        basic_info_score = 0

    # Experience Score (out of 25)
    if experience_analysis:
        exp_scores = [e.score for e in experience_analysis]
        experience_score = sum(exp_scores) / len(exp_scores)
    else:
        experience_score = 0

    # Projects Score (out of 15)
    if projects_analysis:
        proj_scores = [p.score for p in projects_analysis]
        projects_score = sum(proj_scores) / len(proj_scores)
    else:
        projects_score = 0

    # Skills Score (out of 15) - already calculated
    skills_score = skills_analysis.score if skills_analysis else 0

    # Education Score (out of 10) - penalize missing/missing details
    if education_analysis:
        edu_scores = [e.score for e in education_analysis]
        education_score = sum(edu_scores) / len(edu_scores)
    else:
        education_score = 5.0  # STRICT: penalize missing education

    # Achievements & Hobbies Score (out of 10) - penalize missing
    ach_hob_score = (
        achievements_hobbies_analysis.score
        if achievements_hobbies_analysis
        else 5.0  # STRICT: penalize missing achievements
    )

    # Certifications Score (out of 5) - penalize missing
    if certifications_analysis:
        cert_scores = [c.score for c in certifications_analysis]
        certifications_score = sum(cert_scores) / len(cert_scores)
    else:
        certifications_score = 2.5  # STRICT: penalize missing certs

    # Job Role Fit Score - NOT scored, just suggestions
    job_role_fit_score = 0

    # Calculate total (without job role fit)
    total_score = (
        basic_info_score
        + experience_score
        + projects_score
        + skills_score
        + education_score
        + ach_hob_score
        + certifications_score
    )

    # Calculate percentage
    total_percentage = total_score

    # Convert to 100 (job role suggestions get neutral 10 marks)
    converted_percentage = (total_score / 90) * 100 if total_score > 0 else 0

    # Calculate Benchmark Grade (Unified Standard)
    if converted_percentage >= 90:
        grade = "Principal / Director Ready"
    elif converted_percentage >= 80:
        grade = "Senior / Team Lead Ready"
    elif converted_percentage >= 65:
        grade = "Software Engineer II / Mid-Level"
    else:
        grade = "Associate / Junior"

    score_breakdown = ScoreBreakdown(
        basic_info_score=round(basic_info_score, 2),
        experience_score=round(experience_score, 2),
        projects_score=round(projects_score, 2),
        skills_score=round(skills_score, 2),
        education_score=round(education_score, 2),
        achievements_hobbies_score=round(ach_hob_score, 2),
        certifications_score=round(certifications_score, 2),
        job_role_fit_score=0,
        total_score=round(total_score, 2),
        total_percentage=round(total_percentage, 2),
        converted_percentage=round(converted_percentage, 2),
        target_tier="Standard Enterprise",
    )
    score_breakdown.benchmark_grade = grade

    # Get strengths and areas for improvement using LLM
    try:
        prompt = get_consolidator_prompt()
        formatted_prompt = prompt.format(
            **format_consolidator_data(
                basic_info_score,
                experience_score,
                projects_score,
                skills_score,
                education_score,
                ach_hob_score,
                certifications_score,
                job_role_suggestions,
                grade,
            )
        )

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

        result = json.loads(json_str)

        overall_summary = result.get("overall_summary", "Resume analyzed successfully.")
        strengths = result.get("strengths", [])
        areas_for_improvement = result.get("areas_for_improvement", [])

    except Exception as e:
        # Fallback summary
        overall_summary = f"Resume has {len(experience_analysis) if experience_analysis else 0} experience entries and {len(projects_analysis) if projects_analysis else 0} projects. Overall score: {total_percentage:.1f}%"

        strengths = [
            "Clear contact information"
            if basic_info_analysis and basic_info_analysis.email.is_valid
            else "Add contact details",
            f"{len(skills_analysis.skills_list) if skills_analysis else 0} skills listed"
            if skills_analysis and skills_analysis.total_count > 0
            else "Add skills section",
            f"{len(projects_analysis) if projects_analysis else 0} projects showcased"
            if projects_analysis and len(projects_analysis) > 0
            else "Add projects to demonstrate skills",
        ]

        areas_for_improvement = [
            "Review experience descriptions for STAR format",
            "Add quantifiable metrics to achievements",
            "Ensure all skills are reflected in experience/projects",
        ]

    return score_breakdown, overall_summary, strengths, areas_for_improvement, job_role_suggestions
