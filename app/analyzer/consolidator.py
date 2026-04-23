import json
from ..llm.client import llm
from .schemas import ScoreBreakdown, ResumeAnalysis


CONSOLIDATOR_PROMPT = """You are a resume analysis expert. Your task is to consolidate all analysis results and create a final assessment.

Create a final JSON output with:
1. Score Breakdown - calculate all section scores
2. Overall Summary - 3-4 sentence assessment of the resume
3. Strengths - list of resume strengths (3-5) - what the candidate does WELL
4. Areas for Improvement - list of key improvements needed (3-5)

IMPORTANT: Balance your feedback. Don't just list problems - highlight what's good too!

Scoring System (100 total):
- Basic Info: /10
- Experience: /25
- Projects: /15
- Skills: /15
- Education: /10
- Achievements & Hobbies: /5
- Certifications: /10
- Job Role Fit: /10

For each section, calculate percentage based on marks awarded.

Provide overall summary that captures:
- Overall impression
- Key strengths (what's already good)
- Main areas to improve
- Recommendations for next steps

Return JSON with:
{
    "score_breakdown": {...},
    "overall_summary": "...",
    "strengths": ["...", "..."],
    "areas_for_improvement": ["...", "..."]
}"""


def consolidate_analysis(
    basic_info_analysis,
    experience_analysis,
    projects_analysis,
    skills_analysis,
    education_analysis,
    achievements_hobbies_analysis,
    certifications_analysis,
    job_role_suggestions,
    target_tier: str = "Standard Enterprise"
) -> tuple[ScoreBreakdown, str, list[str], list[str], list]:
    """Consolidate all analyses and calculate final scores"""

    # Calculate section scores
    # Basic Info Score (out of 10)
    if basic_info_analysis:
        # Calculate based on field validity
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

    # Education Score (out of 10) - be more lenient
    if education_analysis:
        edu_scores = [e.score for e in education_analysis]
        education_score = sum(edu_scores) / len(edu_scores)
    else:
        education_score = 8.0  # Higher neutral - give benefit of doubt

    # Achievements & Hobbies Score (out of 10) - be more lenient
    ach_hob_score = (
        achievements_hobbies_analysis.score
        if achievements_hobbies_analysis
        else 7.0  # Higher neutral
    )

    # Certifications Score (out of 5) - be more lenient
    if certifications_analysis:
        cert_scores = [c.score for c in certifications_analysis]
        certifications_score = sum(cert_scores) / len(cert_scores)
    else:
        certifications_score = 3.5  # Higher neutral - give benefit of doubt

    # Job Role Fit Score - NOT scored, just suggestions
    # This is just job role suggestions, not a scored section
    job_role_fit_score = 0  # Not counted in total

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

    score_breakdown = ScoreBreakdown(
        basic_info_score=round(basic_info_score, 2),
        experience_score=round(experience_score, 2),
        projects_score=round(projects_score, 2),
        skills_score=round(skills_score, 2),
        education_score=round(education_score, 2),
        achievements_hobbies_score=round(ach_hob_score, 2),
        certifications_score=round(certifications_score, 2),
        job_role_fit_score=0,  # Job suggestions - not scored
        total_score=round(total_score, 2),
        total_percentage=round(total_percentage, 2),
        converted_percentage=round(converted_percentage, 2),
        target_tier=target_tier
    )

    # Calculate Benchmark Grade
    # Tiers: Big Tech, Early Stage Startup, Standard Enterprise, Quant/Research
    grade = "Calculating..."
    if target_tier == "Big Tech (FAAANG)":
        if converted_percentage >= 90: grade = "L6+ / Staff Ready"
        elif converted_percentage >= 82: grade = "L5 / Senior Ready"
        elif converted_percentage >= 70: grade = "L4 / Junior-Mid Ready"
        else: grade = "L3 / Intern-Entry"
    elif target_tier == "Early Stage Startup":
        if converted_percentage >= 85: grade = "Founding Engineer Ready"
        elif converted_percentage >= 75: grade = "Lead / Senior Ready"
        elif converted_percentage >= 65: grade = "Core Contributor"
        else: grade = "Junior / Intern"
    elif target_tier == "Quant/Research":
        if converted_percentage >= 92: grade = "Principal Researcher"
        elif converted_percentage >= 85: grade = "Senior Quantitative Engineer"
        elif converted_percentage >= 75: grade = "Associate Quant"
        else: grade = "Junior Researcher"
    else: # Standard Enterprise
        if converted_percentage >= 88: grade = "Director / Principal"
        elif converted_percentage >= 78: grade = "Senior / Team Lead"
        elif converted_percentage >= 65: grade = "Software Engineer II"
        else: grade = "Associate / Junior"
        
    score_breakdown.benchmark_grade = grade

    # Get strengths and areas for improvement using LLM
    try:
        summary_data = {
            "basic_info_score": basic_info_score,
            "experience_count": len(experience_analysis) if experience_analysis else 0,
            "experience_score": experience_score,
            "projects_count": len(projects_analysis) if projects_analysis else 0,
            "projects_score": projects_score,
            "skills_count": skills_analysis.total_count if skills_analysis else 0,
            "skills_score": skills_score,
            "education_count": len(education_analysis) if education_analysis else 0,
            "education_score": education_score,
            "achievements_count": len(achievements_hobbies_analysis.achievements)
            if achievements_hobbies_analysis
            else 0,
            "certifications_count": len(certifications_analysis)
            if certifications_analysis
            else 0,
            "job_role_suggestions": [r.role for r in job_role_suggestions[:3]]
            if job_role_suggestions
            else [],
            "target_tier": target_tier,
            "benchmark_grade": grade
        }

        prompt = f"""{CONSOLIDATOR_PROMPT}

Analysis Summary:
{json.dumps(summary_data, indent=2)}

Return the JSON object with score_breakdown (filled), overall_summary, strengths, and areas_for_improvement."""

        response = llm.invoke(prompt)
        json_str = response.content.strip()

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
