"""Combined Strategic analyzer (Skills, Job Roles, JD Match) for performance optimization."""
import json
import asyncio
from typing import List, Optional
from ..llm.protocol import LLMClient
from ..llm.utils import parse_llm_json
from ..analyzer.schemas import (
    SkillsAnalysis, AnalysisIssue, JobRoleSuggestion, JDAnalysis
)
from .prompts.skills_prompts import get_skills_prompt, format_skills_data
from .prompts.job_role_suggester_prompts import get_job_role_prompt, format_job_role_data
from .prompts.jd_matcher_prompts import get_jd_matcher_prompt

STRATEGIC_SYSTEM_PROMPT = """You are a career strategy expert specializing in professional enterprise recruiting. Analyze the Skills, Job Role Suggestions, and JD Alignment.

### SKILLS EVALUATION:
Cross-reference listed skills with evidence in Experience and Projects.
- BE CRITICAL. If a skill has NO evidence in experience, penalize heavily.
- Prioritize enterprise-grade technologies (Cloud, Infrastructure, Backend, etc. based on domain).
SCORING (0-15):
- 0-7 (POOR): Lacks core technologies or many skills have NO evidence.
- 8-11 (AVERAGE): Good breadth but missing evidence for 50%+.
- 12-13 (STRONG): Highly relevant stack with clear evidence.
- 14-15 (EXPERT): Mastery of advanced enterprise tech with deep evidence.

### JOB ROLE SUGGESTIONS:
Suggest 3-5 roles. Match score (0-10) based on skills and years of exp.

### JD MATCHING (IF APPLICABLE):
Score 0-100 based on how well the resume meets critical JD requirements.

Return a single JSON object with the following structure:
{{
    "skills_analysis": {{
        "listed_in_exp_projects": [str],
        "missing_from_skills": [str],
        "redundant_skills": [str],
        "issues": [{{ "issue": str, "severity": str, "reason": str }}],
        "suggestions": [str],
        "score": float
    }},
    "job_role_suggestions": [ {{
        "role": str,
        "match_score": float,
        "reasoning": str,
        "suggestions": [str]
    }} ],
    "jd_analysis": {{
        "match_score": float,
        "compatible_roles": [str],
        "missing_critical_skills": [str],
        "missing_nice_to_have": [str],
        "tailoring_recommendations": [str]
    }} (or null if no JD provided)
}}
"""

async def analyze_strategic(resume, llm_client: LLMClient, jd: Optional[str] = None):
    """Analyze Skills, Job Roles, and JD Match in a single LLM call."""
    # Prepare Skills Data
    skills_list = resume.skills or []
    skills_data = format_skills_data(skills_list, resume.experience, resume.projects)
    
    # Prepare Job Role Data
    exp_summary = []
    for exp in resume.experience or []:
        exp_summary.append({"title": exp.title, "company": exp.company, "descriptions": exp.descriptions[:2]})
    proj_summary = []
    for proj in resume.projects or []:
        proj_summary.append({"name": proj.name, "descriptions": proj.descriptions[:2]})
    job_role_data = format_job_role_data(skills_list, exp_summary, proj_summary, resume.total_years_experience or 0)

    prompt = f"{STRATEGIC_SYSTEM_PROMPT}\n\n"
    prompt += f"SKILLS DATA:\n{json.dumps(skills_data, indent=2)}\n\n"
    prompt += f"JOB ROLE CONTEXT:\n{json.dumps(job_role_data, indent=2)}\n\n"
    if jd:
        prompt += f"JOB DESCRIPTION (JD) TO MATCH:\n{jd}\n\n"
    prompt += "Return ONLY the valid JSON object."

    try:
        response = await llm_client.ainvoke(prompt)
        data = parse_llm_json(response)
        
        # 1. Process Skills
        s_data = data.get("skills_analysis", {})
        skills_results = SkillsAnalysis(
            total_count=len(skills_list),
            skills_list=skills_list,
            listed_in_exp_projects=s_data.get("listed_in_exp_projects", []),
            missing_from_skills=s_data.get("missing_from_skills", []),
            redundant_skills=s_data.get("redundant_skills", []),
            issues=[AnalysisIssue(**i) if isinstance(i, dict) else i for i in s_data.get("issues", [])],
            suggestions=s_data.get("suggestions", [])[:3],
            score=max(0, float(s_data.get("score", 12.0))),
        )
        
        # 2. Process Job Roles
        role_results = []
        for s in data.get("job_role_suggestions", []):
            role_results.append(JobRoleSuggestion(
                role=s.get("role", ""),
                match_score=s.get("match_score", 5.0),
                reasoning=s.get("reasoning", ""),
                suggestions=s.get("suggestions", []),
            ))
            
        # 3. Process JD Analysis
        jd_results = None
        if jd and data.get("jd_analysis"):
            j_data = data.get("jd_analysis")
            jd_results = JDAnalysis(
                match_score=j_data.get("match_score", 0.0),
                compatible_roles=j_data.get("compatible_roles", []),
                missing_critical_skills=j_data.get("missing_critical_skills", []),
                missing_nice_to_have=j_data.get("missing_nice_to_have", []),
                tailoring_recommendations=j_data.get("tailoring_recommendations", [])
            )
            
        return skills_results, role_results, jd_results

    except Exception as e:
        print(f"Strategic combined analysis failed: {e}")
        # Return sensible defaults
        return (
            SkillsAnalysis(total_count=len(skills_list), skills_list=skills_list, score=10.0),
            [],
            None
        )
