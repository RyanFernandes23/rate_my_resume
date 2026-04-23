import json
from ..llm.client import llm
from .schemas import EducationAnalysis, GpaAnalysis, AnalysisIssue


EDUCATION_ANALYZER_PROMPT = """You are a resume analysis expert with 10+ years of recruiting experience.

Recruiter Perspective on Education:
1. EDUCATION IS SECONDARY: After 1-2 years of experience, education becomes a checkbox
2. SCANNABILITY: Recruiters spend <5 seconds on education section
3. RELEVANCE: Only relevant for freshers or career changers
4. GPAs MATTER LESS: After 2+ years, work experience outweighs GPA
5. LOCATION: Recruiters may prefer local candidates

Analyze each education entry:
1. Check if institution name is valid and properly formatted
2. Validate dates (start should be before end, should be recent)
3. Evaluate GPA/score - determine if it should be kept or removed
4. Check for location information
5. Consider: Is this relevant for the candidate's career stage?

For each education entry, return a JSON object with:
{
    "entry_index": 0,
    "institution_name_valid": true/false,
    "institution_name": "Institution Name",
    "date_issues": ["issue1", "issue2"],
    "gpa_analysis": {
        "value": "8.5 CGPA" or null,
        "recommendation": "keep/remove",
        "reasoning": "explanation"
    },
    "issues": [{"issue": "description", "severity": "high/medium/low", "reason": "explanation"}],
    "suggestions": ["specific recruiter-focused suggestion referencing actual content"]
}

GPA Recommendation Criteria:
- Keep if: CGPA > 7.5 or percentage > 70% or equivalent good score
- Remove if: CGPA < 6.5 or percentage < 60% or not specified
- Consider context: Some fields (CS, Engineering) expect higher GPAs

Date Validation:
- End date should not be in the future for completed degrees
- Start date should be before end date
- Normal education duration: 2-4 years for bachelor's, 2 years for master's

Analyze all education entries and return a JSON array of analysis objects."""


def analyze_education(resume) -> list[EducationAnalysis]:
    """Analyze all education entries using LLM"""

    if not resume.education:
        return []

    # Build education data for LLM
    edu_data = []
    for i, edu in enumerate(resume.education):
        edu_data.append(
            {
                "index": i,
                "name": edu.name,
                "score": edu.score,
                "start_date": edu.start_date,
                "end_date": edu.end_date,
                "location": edu.location,
            }
        )

    prompt = f"""{EDUCATION_ANALYZER_PROMPT}

Education Data:
{json.dumps(edu_data, indent=2)}

Return a JSON array of analysis objects for each education entry."""

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

        analyses = json.loads(json_str)

        # Convert to EducationAnalysis objects
        result = []
        for analysis in analyses:
            gpa_data = analysis.get("gpa_analysis", {})

            result.append(
                EducationAnalysis(
                    entry_index=analysis.get("entry_index", 0),
                    institution_name_valid=analysis.get("institution_name_valid", True),
                    institution_name=analysis.get("institution_name", ""),
                    date_issues=analysis.get("date_issues", []),
                    gpa_analysis=GpaAnalysis(
                        value=gpa_data.get("value"),
                        recommendation=gpa_data.get("recommendation", "keep"),
                        reasoning=gpa_data.get("reasoning", ""),
                    ),
                    issues=[
                        AnalysisIssue(**issue) for issue in analysis.get("issues", [])
                    ],
                    suggestions=analysis.get("suggestions", []),
                    score=analysis.get("score", 8.0),  # Default score out of 10
                )
            )

        return result

    except Exception as e:
        # Fallback
        result = []
        for i, edu in enumerate(resume.education):
            result.append(
                EducationAnalysis(
                    entry_index=i,
                    institution_name_valid=True,
                    institution_name=edu.name,
                    date_issues=[],
                    gpa_analysis=GpaAnalysis(
                        value=edu.score,
                        recommendation="keep" if edu.score else "remove",
                        reasoning="Based on available data",
                    ),
                    issues=[
                        AnalysisIssue(
                            issue="Could not fully analyze education",
                            severity="low",
                            reason=str(e),
                        )
                    ],
                    suggestions=[],
                    score=8.0,
                )
            )
        return result
