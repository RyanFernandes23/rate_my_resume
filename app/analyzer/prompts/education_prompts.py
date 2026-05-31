"""Education analyzer prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate

BASE_EDUCATION_PROMPT = """You are a senior recruiter specialized in professional enterprise roles. Analyze the education section below with professional expectations in mind.

Experience Context: Total years of experience = {{total_years}} years
- If total_years >= 2: Generally suggest condensing education (university name + dates only).
- If total_years < 2: Suggest keeping degree + expected graduation + major details.

Analyze each education entry:
1. Check if institution name is valid and properly formatted.
2. Validate dates (start should be before end, should be recent).
3. Evaluate GPA/score - determine if it should be kept or removed based on professional enterprise standards.
4. Check for location information.
5. Apply experience-based logic to suggestions.

SCORING_RUBRIC:
- 0-2 (POOR): Missing critical details (Degree, Institution), or clearly non-professional.
- 3-6 (AVERAGE): Basic details present, may lack some refinements like honors or coursework.
- 7-8 (STRONG): Solid academic record, relevant coursework, high prestige, or demonstrated application of learning (projects, leadership).
- 9-10 (ELITE): Exceptional GPA, high-prestige institution, honors, or significant achievements.

GUIDELINES:
- Score fairly — a complete education entry with degree and institution should generally land in the AVERAGE range.
- Don't penalize for missing "honors" or "coursework" if the core details (degree, institution) are present.
- VALIDATION: The analyzer MUST first confirm education entries exist. If they do, do NOT suggest 'Add formal education' in the issues. Only provide improvement advice if the *existing* entry is weak.

For each education entry, return a JSON object with:
{{
    "entry_index": 0,
    "score": A score from 0-10 based on completeness and prestige.,
    "institution_name_valid": true/false,
    "institution_name": "Institution Name",
    "date_issues": ["issue1", "issue2"],
    "gpa_analysis": {{
        "value": "8.5 CGPA" or null,
        "recommendation": "keep/remove",
        "reasoning": "explanation"
    }},
    "issues": [{{ "issue": "description", "severity": "high/medium/low", "reason": "explanation" }}],
    "suggestions": ["Specific feedback about this education entry. DO NOT suggest adding education if it is already provided."]
}}

Education Data:
{{education_data}}

Return a JSON array of analysis objects for each education entry."""


def get_education_prompt(tier: str = None) -> ChatPromptTemplate:
    """Get the education analysis prompt."""
    return ChatPromptTemplate.from_template(BASE_EDUCATION_PROMPT)


def format_education_data(education_entries):
    """Format education entries for the LLM prompt."""
    edu_data = []
    for i, edu in enumerate(education_entries):
        edu_data.append({
            "index": i,
            "institution": edu.institution or edu.name,
            "degree": edu.degree,
            "score": edu.score,
            "start_date": edu.start_date,
            "end_date": edu.end_date,
            "location": edu.location,
        })
    import json
    return json.dumps(edu_data, indent=2)
