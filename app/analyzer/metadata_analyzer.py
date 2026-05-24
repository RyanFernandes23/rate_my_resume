"""Combined Metadata analyzer (Education, Certs, Achievements) for performance optimization."""
import json
import asyncio
from typing import List
from ..llm.protocol import LLMClient
from ..llm.utils import parse_llm_json
from ..analyzer.schemas import (
    EducationAnalysis, GpaAnalysis, AnalysisIssue,
    CertificationAnalysis, AchievementsHobbiesAnalysis,
    AchievementAnalysis, HobbyAnalysis
)
from .prompts.education_prompts import get_education_prompt, format_education_data
from .prompts.certifications_prompts import get_certifications_prompt, format_certifications_data
from .prompts.achievements_prompts import get_achievements_prompt, format_achievements_data

METADATA_SYSTEM_PROMPT = """You are a senior recruiter specialized in professional enterprise roles. Analyze the Education, Certifications, and Achievements/Hobbies sections of this resume.

### EDUCATION EVALUATION:
IMPORTANT: If education entries exist, do NOT suggest "Add formal education". Only give feedback on how to improve existing entries.
- If exp >= 2 years: Suggest condensing.
- If exp < 2 years: Keep details.
SCORING (0-10):
- 0-3 (POOR): Missing major/degree, unrecognizable institution.
- 4-6 (AVERAGE): Recognized university but average performance.
- 7-8 (STRONG): High GPA, relevant major, recognized institution.
- 9-10 (EXPERT): Top-tier/Elite (Ivy, MIT, IIT) with exceptional honors.

### CERTIFICATIONS EVALUATION:
Check for industry-recognized providers (AWS, Google, Microsoft, CFA, etc.).
SCORING (0-5):
- 0-1 (POOR): Irrelevant or low-quality certification from unknown issuer. No link or date.
- 2-3 (AVERAGE): Recognized certification but from a lower-tier provider or missing details.
- 4 (STRONG): Industry-recognized certification with proper details.
- 5 (EXPERT): High-impact, advanced certification from a top-tier provider with all details present.

### ACHIEVEMENTS & HOBBIES EVALUATION:
- Achievements: Look for quantifiable impact and professional relevance.
- Hobbies: Note if they are professional-relevant or just personal.
SCORING (0-10):
- Achievements (6pts): 0.75pt each for up to 4.
- Hobbies (4pts): 1pt each for up to 4.

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
    "hobbies": [ {{
        "hobby": str,
        "is_professional": bool,
        "suggestions": [str]
    }} ],
    "overall_metadata_suggestions": [str]
}}
"""

async def analyze_metadata(resume, llm_client: LLMClient):
    """Analyze Education, Certifications, and Achievements in a single LLM call."""
    # Prepare combined data
    edu_data = format_education_data(resume.education) if resume.education else "[]"
    cert_data = format_certifications_data(resume.certifications) if resume.certifications else "[]"
    ach_data = format_achievements_data(resume.achievements, resume.hobbies, resume.extra_curricular)
    
    # Calculate years of exp for education context
    total_years = resume.total_years_experience or 0

    prompt = f"{METADATA_SYSTEM_PROMPT}\n\n"
    prompt += f"TOTAL YEARS EXPERIENCE: {total_years}\n\n"
    prompt += f"EDUCATION DATA:\n{edu_data}\n\n"
    prompt += f"CERTIFICATIONS DATA:\n{cert_data}\n\n"
    prompt += f"ACHIEVEMENTS DATA:\n{ach_data['achievements_data']}\n\n"
    prompt += f"HOBBIES DATA:\n{ach_data['hobbies_data']}\n\n"
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
            
        # 3. Process Achievements & Hobbies
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
            
        hobby_results = []
        for hb in data.get("hobbies", []):
            hobby_results.append(HobbyAnalysis(
                hobby=hb.get("hobby", ""),
                is_professional=hb.get("is_professional", False),
                suggestions=hb.get("suggestions", []),
            ))
            
        # Calculate combined Achievements score
        ach_count = len(ach_results)
        hobby_count = len(hobby_results)
        ach_score = min(6.0, ach_count * 0.75) if ach_count > 0 else 0.0
        hobby_score = min(4.0, hobby_count * 1.0)
            
        ach_hobbies_final = AchievementsHobbiesAnalysis(
            achievements=ach_results,
            hobbies=hobby_results,
            suggestions=data.get("overall_metadata_suggestions", []),
            score=round(ach_score + hobby_score, 2)
        )
        
        return edu_results, cert_results, ach_hobbies_final

    except Exception as e:
        print(f"Metadata combined analysis failed: {e}. Falling back to defaults.")
        # Simplified fallback - you could import and call original fallbacks here
        return [], [], AchievementsHobbiesAnalysis(achievements=[], hobbies=[], suggestions=[], score=0.0)
