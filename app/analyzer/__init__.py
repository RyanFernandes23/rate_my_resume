from .schemas import ResumeAnalysis
from .basic_validator import analyze_basic_info
from .experience_analyzer import analyze_experience
from .projects_analyzer import analyze_projects
from .skills_analyzer import analyze_skills
from .education_analyzer import analyze_education
from .achievements_hobbies_analyzer import analyze_achievements_hobbies
from .certifications_analyzer import analyze_certifications
from .job_role_suggester import suggest_job_roles
from .consolidator import consolidate_analysis


def analyze_resume(resume, jd: str = None, target_tier: str = "Standard Enterprise") -> ResumeAnalysis:
    """Main entry point - analyze resume using all analyzer nodes"""

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

    # Run all analyzer nodes sequentially
    print("Running Basic Info Validator...")
    basic_info_analysis = analyze_basic_info(resume)

    print("Running Experience Analyzer...")
    experience_analysis = analyze_experience(resume)

    print("Running Projects Analyzer...")
    projects_analysis = analyze_projects(resume)

    print("Running Skills Analyzer...")
    skills_analysis = analyze_skills(resume)

    print("Running Education Analyzer...")
    education_analysis = analyze_education(resume)

    print("Running Achievements & Hobbies Analyzer...")
    achievements_hobbies_analysis = analyze_achievements_hobbies(resume)

    print("Running Certifications Analyzer...")
    certifications_analysis = analyze_certifications(resume)

    print("Running Job Role Suggester...")
    job_role_suggestions = suggest_job_roles(resume)

    print("Running JD Matcher...")
    jd_analysis = match_with_jd(resume, jd) if jd else None

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
            target_tier=target_tier
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
        jd_analysis=jd_analysis
    )
