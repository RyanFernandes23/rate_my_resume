import json
from ..llm.client import llm
from .schemas import SkillsAnalysis, AnalysisIssue


SKILLS_ANALYZER_PROMPT = """You are a resume analysis expert with 10+ years of recruiting experience.

Recruiter Perspective on Skills:
1. ATS SCANNING: Most ATS systems search for skills keywords - list them!
2. QUICK SCAN: Recruiters scan for 2-3 seconds looking for key tech stacks
3. RELEVANCE: Skills should match the job description keywords
4. GROUPING: Categorized skills (Languages, Frameworks, Tools) are easier to scan
5. FRESHERS vs EXPERIENCED: Freshers need more skills listed; experienced need them aligned with work

Analyze the skills section and cross-reference with experience and projects:

1. Check if skills mentioned in experience and projects are listed in the skills section
2. Identify skills used in exp/proj but NOT in skills list (missing)
3. Identify skills in skills list but NOT used in exp/proj (redundant)
4. Evaluate skill variety and relevance

Return a JSON object with:
{
    "total_count": number,
    "skills_list": ["skill1", "skill2"],
    "listed_in_exp_projects": ["skill1", "skill2"],
    "missing_from_skills": ["skill1", "skill2"],
    "redundant_skills": ["skill1", "skill2"],
    "issues": [{"issue": "description", "severity": "high/medium/low", "reason": "explanation"}],
    "suggestions": ["specific recruiter-focused suggestion: 'You used X in your project but didn't list it in skills - add it for ATS visibility'"]
}

Evaluation Criteria:
- Missing skills (high severity): Skills explicitly used in projects/experience but not listed
- Redundant skills (low severity): Listed but never mentioned in exp/proj
- Low count (medium): Less than 10 skills might be too few
- No categorization: Skills grouped by type (languages, frameworks, tools) is better

Analyze skills and return a JSON object."""


def analyze_skills(resume) -> SkillsAnalysis:
    """Analyze skills with cross-reference to experience and projects"""

    skills_list = resume.skills or []
    total_count = len(skills_list)

    # Use LLM for more accurate cross-reference
    prompt = f"""{SKILLS_ANALYZER_PROMPT}

Resume Skills:
{json.dumps(skills_list, indent=2)}

Experience Descriptions:
{json.dumps([desc for exp in (resume.experience or []) for desc in (exp.descriptions or [])], indent=2)}

Project Descriptions:
{json.dumps([desc for proj in (resume.projects or []) for desc in (proj.descriptions or [])], indent=2)}

Return a JSON object with the analysis."""

    try:
        response = llm.invoke(prompt)
        json_str = response.content.strip()

        # Clean up markdown
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        elif json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()

        analysis = json.loads(json_str)

        # Calculate score (out of 15) - MORE LENIENT
        score = 15.0

        # Only deduct for critical issues (truly missing skills that are core)
        missing_count = len(analysis.get("missing_from_skills", []))
        if missing_count > 5:  # Only if more than 5 truly missing
            score -= min(2.0, (missing_count - 5) * 0.3)

        # Be lenient on skill count
        if total_count < 5:
            score -= 2.0
        elif total_count < 10:
            score -= 0.5

        # Don't penalize for "redundant" skills - listing extra skills is fine
        # This is actually good, not bad

        return SkillsAnalysis(
            total_count=total_count,
            skills_list=skills_list,
            listed_in_exp_projects=analysis.get("listed_in_exp_projects", []),
            missing_from_skills=analysis.get("missing_from_skills", []),
            redundant_skills=[],  # Don't flag as issue
            issues=[
                AnalysisIssue(
                    issue="Consider adding any missing skills from projects",
                    severity="low",
                    reason="Some project technologies may not be listed",
                )
            ]
            if missing_count > 0
            else [],
            suggestions=analysis.get("suggestions", [])[:1]
            if analysis.get("suggestions")
            else [],
            score=max(0, score),
        )

    except Exception as e:
        # Default good score if skills exist
        if total_count > 0:
            return SkillsAnalysis(
                total_count=total_count,
                skills_list=skills_list,
                listed_in_exp_projects=[],
                missing_from_skills=[],
                redundant_skills=[],
                issues=[],
                suggestions=[],
                score=14.0,  # Good default if skills present
            )
        else:
            return SkillsAnalysis(
                total_count=0,
                skills_list=[],
                listed_in_exp_projects=[],
                missing_from_skills=[],
                redundant_skills=[],
                issues=[
                    AnalysisIssue(
                        issue="No skills listed",
                        severity="high",
                        reason="Skills section is empty",
                    )
                ],
                suggestions=["Add a skills section with your technical competencies"],
                score=5.0,
            )
