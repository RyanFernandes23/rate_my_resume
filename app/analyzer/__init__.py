"""Main resume analysis module using LangChain and externalized prompts."""
from .schemas import ResumeAnalysis
from .basic_validator import analyze_basic_info
from .experience_analyzer import analyze_experience
from .projects_analyzer import analyze_projects
from .skills_analyzer import analyze_skills
from .education_analyzer import analyze_education
from .achievements_hobbies_analyzer import analyze_achievements_hobbies
from .certifications_analyzer import analyze_certifications
from .job_role_suggester import suggest_job_roles
from .jd_matcher import match_with_jd
from .consolidator import consolidate_analysis


def analyze_resume(resume, jd: str = None, target_tier: str = "Standard Enterprise") -> ResumeAnalysis:
    """Main entry point - analyze resume using all analyzer nodes with externalized prompts."""

    # Run all analyzer nodes sequentially
    print(f"Running Basic Info Validator for {target_tier}...")
    basic_info_analysis = analyze_basic_info(resume)

    print(f"Running Experience Analyzer for {target_tier}...")
    experience_analysis = analyze_experience(resume, target_tier=target_tier)

    print(f"Running Projects Analyzer for {target_tier}...")
    projects_analysis = analyze_projects(resume, target_tier=target_tier)

    print(f"Running Skills Analyzer for {target_tier}...")
    skills_analysis = analyze_skills(resume, target_tier=target_tier)

    print(f"Running Education Analyzer for {target_tier}...")
    education_analysis = analyze_education(resume, tier=target_tier)

    print(f"Running Achievements & Hobbies Analyzer for {target_tier}...")
    achievements_hobbies_analysis = analyze_achievements_hobbies(resume, tier=target_tier)

    print(f"Running Certifications Analyzer for {target_tier}...")
    certifications_analysis = analyze_certifications(resume, tier=target_tier)

    print(f"Running Job Role Suggester for {target_tier}...")
    job_role_suggestions = suggest_job_roles(resume, tier=target_tier)

    print(f"Running JD Matcher for {target_tier}...")
    jd_analysis = match_with_jd(resume, jd, tier=target_tier) if jd else None

    print("Consolidating results...")
    score_breakdown, overall_summary, strengths, areas_for_improvement, job_role_suggestions = (
        consolidate_analysis(
            basic_info_analysis,
            experience_analysis,
            projects_analysis,
            skills_analysis,
            education_analysis,
            achievements_hobbies_analysis,
            certifications_analysis,
            job_role_suggestions,
            target_tier=target_tier,
        )
    )

    return ResumeAnalysis(
        score_breakdown=score_breakdown,
        basic_info_analysis=basic_info_analysis,
        experience_analysis=experience_analysis,
        projects_analysis=projects_analysis,
        skills_analysis=skills_analysis,
        education_analysis=education_analysis,
        achievements_hobbies_analysis=achievements_hobbies_analysis,
        certifications_analysis=certifications_analysis,
        job_role_suggestions=job_role_suggestions,
        overall_summary=overall_summary,
        strengths=strengths,
        areas_for_improvement=areas_for_improvement,
        jd_analysis=jd_analysis,
    )
