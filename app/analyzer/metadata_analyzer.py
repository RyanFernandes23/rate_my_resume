"""Combined Metadata analyzer (Education, Certs, Achievements) for performance optimization."""
import json
import asyncio
from typing import List
from ..llm.protocol import LLMClient
from ..llm.utils import parse_llm_json
from ..analyzer.schemas import (
    EducationAnalysis, GpaAnalysis, AnalysisIssue,
    CertificationAnalysis, AchievementsAnalysis,
    AchievementAnalysis
)
from .prompts.education_prompts import get_education_prompt, format_education_data
from .prompts.certifications_prompts import get_certifications_prompt, format_certifications_data
from .prompts.achievements_prompts import get_achievements_prompt, format_achievements_data

METADATA_SYSTEM_PROMPT = """You are a senior recruiter specialized in professional enterprise roles. Analyze the Education, Certifications, and Achievements/Hobbies sections of this resume.

### EDUCATION EVALUATION:
IMPORTANT: If education entries exist, do NOT suggest \"Add formal education\". Only give feedback on how to improve existing entries.
- If exp >= 2 years: Suggest condensing (institution name + dates only).
- If exp < 2 years: Check for degree, institution, and performance details.
SCORING (0-10):
- 0-2 (POOR): Missing critical details like Degree or Institution name.
- 3-6 (AVERAGE): Basic details present, may lack some refinements.
- 7-8 (STRONG): Solid academic record, clear degree/major, recognized institution.
- 9-10 (EXPERT): Top-tier/Elite (Ivy, MIT, IIT, IIM) with exceptional honors.

### CERTIFICATIONS EVALUATION:
Check for industry-recognized providers (AWS, Google, Microsoft, CFA, etc.).
SCORING (0-5):
- 0-1 (POOR): Irrelevant or low-quality certification from unknown issuer.
- 2-3 (AVERAGE): Recognized certification with basic details present.
- 4 (STRONG): Industry-recognized certification with proper details.
- 5 (EXPERT): High-impact, advanced certification from a top-tier provider with all details present.

### ACHIEVEMENTS EVALUATION:
- Look for real-world impact, recognition, and professional relevance.
SCORING (0-10):
- Achievements (10pts): up to 10 points based on quality and impact.

Return a single JSON object with the following structure:
{{
    "education": [ {{ 
        "entry_index": int,
        "score": float,
        "institution_name_valid": bool,
        "institution_name": str,
        "date_issues": [str],
        "gpa_analysis": {{ "value": str, "recommendation": str, "reasoning": str }},
        "issues": [{{ "issue": str, "severity": str, "reason": str }}],
        "suggestions": [str]
    }} ],
    "certifications": [ {{
        "index": int,
        "name": str,
        "is_valid": bool,
        "organization_issues": [str],
        "date_issues": [str],
        "link_issues": [str],
        "suggestions": [str],
        "score": float
    }} ],
    "achievements": [ {{
        "index": int,
        "title": str,
        "impact_score": float,
        "recommendation": str,
        "reasoning": str,
        "issues": [str]
    }} ],

    "overall_metadata_suggestions": [str]
}}
"""

async def analyze_metadata(resume, llm_client: LLMClient, target_tier: str = "fresher"):
    """Analyze Education, Certifications, and Achievements in a single LLM call."""
    # Prepare combined data
    edu_data = format_education_data(resume.education) if resume.education else "[]"
    cert_data = format_certifications_data(resume.certifications) if resume.certifications else "[]"
    ach_data = format_achievements_data(resume.achievements, resume.hobbies, resume.extra_curricular)
    
    # Calculate years of exp for education context
    total_years = resume.total_years_experience or 0

    tier_context = "Fresher (0-2 years) — education and certifications are central. Score them generously for completeness and relevance. Achievements showing initiative and potential are highly valued."
    if target_tier == "experienced":
        tier_context = "Experienced (3+ years) — education is background context; experience trumps it. Certifications and achievements should demonstrate advanced, applied expertise."

    prompt = f"{METADATA_SYSTEM_PROMPT}\n\n"
    prompt += f"CANDIDATE TIER: {tier_context}\n\n"
    prompt += f"TOTAL YEARS EXPERIENCE: {total_years}\n\n"
    prompt += f"EDUCATION DATA:\n{edu_data}\n\n"
    prompt += f"CERTIFICATIONS DATA:\n{cert_data}\n\n"
    prompt += f"ACHIEVEMENTS DATA:\n{ach_data}\n\n"
    prompt += "Return ONLY the valid JSON object."

    try:
        response = await llm_client.ainvoke(prompt)
        data = parse_llm_json(response)
        
        # 1. Process Education
        edu_results = []
        for analysis in data.get("education", []):
            idx = analysis.get("entry_index", 0)
            edu = resume.education[idx] if idx < len(resume.education) else None
            gpa_data = analysis.get("gpa_analysis", {})
            edu_results.append(EducationAnalysis(
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
            ))
            
        # 2. Process Certifications
        cert_results = []
        for c in data.get("certifications", []):
            cert_results.append(CertificationAnalysis(
                index=c.get("index", 0),
                name=c.get("name", ""),
                is_valid=c.get("is_valid", True),
                organization_issues=c.get("organization_issues", []),
                date_issues=c.get("date_issues", []),
                link_issues=c.get("link_issues", []),
                suggestions=c.get("suggestions", []),
                score=float(c.get("score", 4.0)),
            ))
            
        # 3. Process Achievements
        ach_results = []
        for ach in data.get("achievements", []):
            ach_results.append(AchievementAnalysis(
                index=ach.get("index", 0),
                title=ach.get("title", ""),
                impact_score=ach.get("impact_score", 5.0),
                recommendation=ach.get("recommendation", "keep"),
                reasoning=ach.get("reasoning", ""),
                issues=ach.get("issues", []),
            ))
            
        # Calculate Achievements score
        ach_count = len(ach_results)
        ach_score = min(10.0, ach_count * 1.5) if ach_count > 0 else 0.0
            
        ach_final = AchievementsAnalysis(
            achievements=ach_results,
            suggestions=data.get("overall_metadata_suggestions", []),
            score=round(ach_score, 2)
        )
        
        return edu_results, cert_results, ach_final

    except Exception as e:
        print(f"Metadata combined analysis failed: {e}. Falling back to defaults.")
        # Simplified fallback - you could import and call original fallbacks here
        return [], [], AchievementsAnalysis(achievements=[], suggestions=[], score=0.0)
