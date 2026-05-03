"""Main resume analysis module using LangChain and externalized prompts."""
import asyncio
from .schemas import ResumeAnalysis
from .basic_validator import analyze_basic_info
from .experience_analyzer import analyze_experience
from .projects_analyzer import analyze_projects
from .metadata_analyzer import analyze_metadata
from .strategic_analyzer import analyze_strategic
from .consolidator import consolidate_analysis


async def analyze_resume(resume, jd: str = None) -> ResumeAnalysis:
    """Main entry point - analyze resume using all analyzer nodes in parallel."""

    # 1. Run Basic Info Validator (Sync/Fast)
    print("Running Basic Info Validator...")
    basic_info_analysis = analyze_basic_info(resume)

    # 2. Run LLM Analyzers in Parallel
    print("Starting Parallel LLM Analysis (Experience, Projects, Metadata, Strategy)...")
    
    # Define tasks
    tasks = [
        analyze_experience(resume),
        analyze_projects(resume),
        analyze_metadata(resume),
        analyze_strategic(resume, jd)
    ]
    
    # Execute and wait for all to complete
    results = await asyncio.gather(*tasks)
    
    experience_analysis = results[0]
    projects_analysis = results[1]
    education_analysis, certifications_analysis, achievements_hobbies_analysis = results[2]
    skills_analysis, job_role_suggestions, jd_analysis = results[3]

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
