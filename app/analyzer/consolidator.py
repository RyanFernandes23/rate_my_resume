"""Consolidator using LangChain and externalized prompts."""
import json
import re
from ..llm.protocol import LLMClient
from ..analyzer.schemas import ScoreBreakdown, ResumeAnalysis
from .prompts.consolidator_prompts import get_consolidator_prompt, format_consolidator_data


def _calculate_tiered_score(
    basic_info_score, experience_score, projects_score,
    skills_score, education_score, ach_score, certifications_score,
    target_tier="fresher",
):
    CORE_SECTIONS = {"basic_info", "experience", "skills"}

    if target_tier == "experienced":
        SUPP_THRESHOLD = 0.35
    else:
        SUPP_THRESHOLD = 0.2

    section_weights = [
        (basic_info_score, 10, "basic_info"),
        (experience_score, 25, "experience"),
        (projects_score, 25, "projects"),
        (skills_score, 15, "skills"),
        (education_score, 10, "education"),
        (ach_score, 10, "achievements"),
        (certifications_score, 5, "certifications"),
    ]

    active_score = 0.0
    active_max = 0.0
    for score, max_score, name in section_weights:
        if name in CORE_SECTIONS or (max_score > 0 and score / max_score >= SUPP_THRESHOLD):
            active_score += score
            active_max += max_score

    return active_score, active_max


async def consolidate_analysis(
    llm_client: LLMClient,
    basic_info_analysis,
    experience_analysis,
    projects_analysis,
    skills_analysis,
    education_analysis,
    achievements_analysis,
    certifications_analysis,
    job_role_suggestions,
    target_tier: str = "fresher",
):
    """Consolidate all analyses and calculate final scores."""

    # Calculate section scores
    # Basic Info Score (out of 10)
    if basic_info_analysis:
        bi_score = 10.0
        if not basic_info_analysis.name.is_valid:
            bi_score -= 1
        if not basic_info_analysis.email.is_valid:
            bi_score -= 1
        if not basic_info_analysis.phone.is_valid:
            bi_score -= 1
        if not basic_info_analysis.links.is_valid:
            bi_score -= 1
        basic_info_score = max(0, bi_score)
    else:
        basic_info_score = 0

    # Experience Score (out of 25)
    if experience_analysis:
        exp_scores = [e.score for e in experience_analysis]
        experience_score = sum(exp_scores) / len(exp_scores)
    else:
        experience_score = 0

    # Projects Score (out of 25)
    if projects_analysis:
        proj_scores = [p.score for p in projects_analysis]
        projects_score = sum(proj_scores) / len(proj_scores)
    else:
        projects_score = 0

    # Skills Score (out of 15) - already calculated
    skills_score = skills_analysis.score if skills_analysis else 0

    # Education Score (out of 10)
    if education_analysis:
        edu_scores = [e.score for e in education_analysis]
        education_score = sum(edu_scores) / len(edu_scores)
        education_status = f"Found {len(education_analysis)} entries (score {education_score:.1f}/10)"
    else:
        education_score = 0
        education_status = "Not found (score 0/10)"

    # Achievements Score (out of 10)
    ach_score = (
        achievements_analysis.score
        if achievements_analysis
        else 0
    )
    achievements_status = (
        f"Found {len(achievements_analysis.achievements)} achievements (score {ach_score:.1f}/10)"
        if achievements_analysis
        else "Not found (score 0/10)"
    )

    # Certifications Score (out of 5)
    if certifications_analysis:
        cert_scores = [c.score for c in certifications_analysis]
        certifications_score = sum(cert_scores) / len(cert_scores)
        certifications_status = f"Found {len(certifications_analysis)} entries (score {certifications_score:.1f}/5)"
    else:
        certifications_score = 0
        certifications_status = "Not found (score 0/5)"

    # Job Role Fit Score - NOT scored, just suggestions
    job_role_fit_score = 0

    active_score, active_max = _calculate_tiered_score(
        basic_info_score,
        experience_score,
        projects_score,
        skills_score,
        education_score,
        ach_score,
        certifications_score,
        target_tier=target_tier,
    )

    total_percentage = (active_score / active_max * 100) if active_max > 0 else 0.0
    total_score = total_percentage
    converted_percentage = total_percentage if total_percentage > 0 else 0

    # Calculate Benchmark Grade (Tier-Aware)
    if target_tier == "experienced":
        if converted_percentage >= 90:
            grade = "Principal / Director Ready"
        elif converted_percentage >= 80:
            grade = "Senior / Team Lead Ready"
        elif converted_percentage >= 60:
            grade = "Software Engineer II / Mid-Level"
        else:
            grade = "Associate / Junior"
    else:
        # Fresher: lower bars — less experience needed to reach each grade
        if converted_percentage >= 80:
            grade = "Principal / Director Ready"
        elif converted_percentage >= 70:
            grade = "Senior / Team Lead Ready"
        elif converted_percentage >= 50:
            grade = "Software Engineer II / Mid-Level"
        else:
            grade = "Associate / Junior"

    tier_label = "Fresher (0-2 years)" if target_tier == "fresher" else "Experienced (3+ years)"
    score_breakdown = ScoreBreakdown(
        basic_info_score=round(basic_info_score, 2),
        experience_score=round(experience_score, 2),
        projects_score=round(projects_score, 2),
        skills_score=round(skills_score, 2),
        education_score=round(education_score, 2),
        achievements_score=round(ach_score, 2),
        certifications_score=round(certifications_score, 2),
        job_role_fit_score=0,
        total_score=round(total_score, 2),
        total_percentage=round(total_percentage, 2),
        converted_percentage=round(converted_percentage, 2),
        target_tier=tier_label,
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
                ach_score,
                certifications_score,
                job_role_suggestions,
                grade,
                education_status=education_status,
                certifications_status=certifications_status,
                achievements_status=achievements_status,
            )
        )

        response = await llm_client.ainvoke(formatted_prompt)
        json_str = response.strip()

        # Extract JSON object from potential markdown fences / preamble text
        fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', json_str, re.DOTALL)
        if fence_match:
            json_str = fence_match.group(1).strip()
        else:
            brace_match = re.search(r'\{.*\}', json_str, re.DOTALL)
            if brace_match:
                json_str = brace_match.group(0).strip()

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
