"""Main resume analysis module using LangChain and externalized prompts."""
import asyncio
import logging
import time
from ..llm.protocol import LLMClient
from .schemas import ResumeAnalysis
from .basic_validator import analyze_basic_info
from .experience_analyzer import analyze_experience
from .projects_analyzer import analyze_projects
from .metadata_analyzer import analyze_metadata
from .strategic_analyzer import analyze_strategic
from .consolidator import consolidate_analysis

logger = logging.getLogger(__name__)


async def analyze_resume(resume, llm_client: LLMClient, fast_llm_client: LLMClient = None, jd: str = None) -> ResumeAnalysis:
    _t0 = time.perf_counter()

    basic_info_analysis = analyze_basic_info(resume)
    logger.info("[TIMING] basic_info (local): %.4fs", time.perf_counter() - _t0)

    fast = llm_client

    _t = time.perf_counter()
    tasks = [
        analyze_experience(resume, llm_client),
        analyze_projects(resume, llm_client),
        analyze_metadata(resume, fast),
        analyze_strategic(resume, fast, jd),
    ]

    results = await asyncio.gather(*tasks)
    logger.info("[TIMING] all 4 parallel analyzers: %.2fs", time.perf_counter() - _t)
    
    experience_analysis = results[0]
    projects_analysis = results[1]
    education_analysis, certifications_analysis, achievements_analysis = results[2]
    skills_analysis, job_role_suggestions, jd_analysis = results[3]

    _t = time.perf_counter()
    score_breakdown, overall_summary, strengths, areas_for_improvement, job_role_suggestions = (
        await consolidate_analysis(
            llm_client,
            basic_info_analysis,
            experience_analysis,
            projects_analysis,
            skills_analysis,
            education_analysis,
            achievements_analysis,
            certifications_analysis,
            job_role_suggestions,
        )
    )
    logger.info("[TIMING] consolidate: %.2fs", time.perf_counter() - _t)

    logger.info("[TIMING] TOTAL analyzers: %.2fs", time.perf_counter() - _t0)
    return ResumeAnalysis(
        score_breakdown=score_breakdown,
        basic_info_analysis=basic_info_analysis,
        experience_analysis=experience_analysis,
        projects_analysis=projects_analysis,
        skills_analysis=skills_analysis,
        education_analysis=education_analysis,
        achievements_analysis=achievements_analysis,
        certifications_analysis=certifications_analysis,
        job_role_suggestions=job_role_suggestions,
        overall_summary=overall_summary,
        strengths=strengths,
        areas_for_improvement=areas_for_improvement,
        jd_analysis=jd_analysis,
    )
