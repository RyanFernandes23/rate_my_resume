"""Education analyzer prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate

ENTERPRISE_GUIDANCE = """Evaluate education based on the candidate's domain with professional enterprise standards. Adapt criteria accordingly:

TECHNOLOGY & ENGINEERING:
- High emphasis on technical universities and top-tier CS/Engineering programs.
- GPA: Keep if > 8.0 CGPA; note if lower.
- Relevant Coursework: Distributed Systems, Algorithms, OS, Machine Learning, Cloud Computing.
- Look for internships at tech companies or notable projects.

FINANCE & BANKING:
- High emphasis on target schools (Ivy League, top business schools, finance-focused institutions).
- GPA: Keep if > 3.5/4.0 or equivalent; highly competitive.
- Relevant: Finance, Economics, Mathematics, Quantitative methods.
- Look for CFA, FRM certifications or relevant coursework.

CONSULTING:
- Emphasis on top-tier business schools or prestigious undergraduate institutions.
- GPA: Keep if > 3.5/4.0; consulting firms are selective.
- Relevant: Strategy, Operations, Economics, Business Analytics.
- Look for case competition experience or consulting internships.

PRODUCT MANAGEMENT:
- Flexible on school prestige; focus on practical skills and product mindset.
- GPA: Keep if > 7.5 CGPA or 3.0/4.0; not a dealbreaker.
- Relevant: Business, CS, Design, or interdisciplinary programs.
- Look for product internships or relevant projects.

MARKETING & GROWTH:
- Flexible on school prestige; focus on creativity and results.
- GPA: Keep if > 7.0 CGPA or 3.0/4.0.
- Relevant: Marketing, Communications, Digital Media, Business.
- Look for marketing internships, campaigns, or portfolio work.

DATA SCIENCE & ML:
- Strong emphasis on quantitative backgrounds.
- GPA: Keep if > 8.0 CGPA or 3.5/4.0.
- Relevant: Statistics, Mathematics, CS, Data Science, Physics.
- Look for research experience, ML projects, or Kaggle competitions.

SALES & BUSINESS DEVELOPMENT:
- Flexible on education; focus on interpersonal skills and track record.
- GPA: Keep if > 6.5 CGPA or 2.8/4.0; less critical.
- Relevant: Business, Communications, International Relations.
- Look for sales experience, leadership roles, or extracurriculars.

OPERATIONS & SUPPLY CHAIN:
- Focus on supply chain, operations, or engineering backgrounds.
- GPA: Keep if > 7.5 CGPA or 3.0/4.0.
- Relevant: Engineering, Operations Management, Logistics, Business.
- Look for internships in operations, logistics, or process improvement.

Provide domain-appropriate evaluation and recommendations."""

BASE_EDUCATION_PROMPT = """You are a senior recruiter specialized in professional enterprise roles. Analyze the education section below with production-grade enterprise expectations in mind.

Recruiter Perspective on Education:
Evaluate education based on the candidate's domain with professional enterprise standards. Adapt criteria accordingly:

TECHNOLOGY & ENGINEERING:
- High emphasis on technical universities and top-tier CS/Engineering programs.
- GPA: Keep if > 8.0 CGPA; note if lower.
- Relevant Coursework: Distributed Systems, Algorithms, OS, Machine Learning, Cloud Computing.
- Look for internships at tech companies or notable projects.

FINANCE & BANKING:
- High emphasis on target schools (Ivy League, top business schools, finance-focused institutions).
- GPA: Keep if > 3.5/4.0 or equivalent; highly competitive.
- Relevant: Finance, Economics, Mathematics, Quantitative methods.
- Look for CFA, FRM certifications or relevant coursework.

CONSULTING:
- Emphasis on top-tier business schools or prestigious undergraduate institutions.
- GPA: Keep if > 3.5/4.0; consulting firms are selective.
- Relevant: Strategy, Operations, Economics, Business Analytics.
- Look for case competition experience or consulting internships.

PRODUCT MANAGEMENT:
- Flexible on school prestige; focus on practical skills and product mindset.
- GPA: Keep if > 7.5 CGPA or 3.0/4.0; not a dealbreaker.
- Relevant: Business, CS, Design, or interdisciplinary programs.
- Look for product internships or relevant projects.

MARKETING & GROWTH:
- Flexible on school prestige; focus on creativity and results.
- GPA: Keep if > 7.0 CGPA or 3.0/4.0.
- Relevant: Marketing, Communications, Digital Media, Business.
- Look for marketing internships, campaigns, or portfolio work.

DATA SCIENCE & ML:
- Strong emphasis on quantitative backgrounds.
- GPA: Keep if > 8.0 CGPA or 3.5/4.0.
- Relevant: Statistics, Mathematics, CS, Data Science, Physics.
- Look for research experience, ML projects, or Kaggle competitions.

SALES & BUSINESS DEVELOPMENT:
- Flexible on education; focus on interpersonal skills and track record.
- GPA: Keep if > 6.5 CGPA or 2.8/4.0; less critical.
- Relevant: Business, Communications, International Relations.
- Look for sales experience, leadership roles, or extracurriculars.

OPERATIONS & SUPPLY CHAIN:
- Focus on supply chain, operations, or engineering backgrounds.
- GPA: Keep if > 7.5 CGPA or 3.0/4.0.
- Relevant: Engineering, Operations Management, Logistics, Business.
- Look for internships in operations, logistics, or process improvement.

Provide domain-appropriate evaluation and recommendations.

Experience Context: Total years of experience = {{total_years}} years
- If total_years >= 2: Generally suggest condensing education (university name + dates only).
- If total_years < 2: Suggest keeping degree + expected graduation + major details.

Analyze each education entry:
1. Check if institution name is valid and properly formatted.
2. Validate dates (start should be before end, should be recent).
3. Evaluate GPA/score - determine if it should be kept or removed based on professional enterprise standards.
4. Check for location information.
5. Apply experience-based logic to suggestions.

SCORING_RUBRIC (STRICT):
- 0-3 (POOR): Missing critical details (Degree, Institution), or clearly non-professional.
- 4-6 (AVERAGE): Basic details present, but lacks relevant coursework, honors, or prestige.
- 7-8 (STRONG): Solid academic record, relevant coursework mentioned, or high prestige.
- 9-10 (ELITE): Exceptional GPA, high-prestige institution, honors, or significant relevant achievements.

STRICTNESS RULES:
- BE CRITICAL. Scoring should be normalized so a 'good' resume gets a 7.
- Penalize heavily for missing details if entry is present.
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
            "name": edu.name,
            "score": edu.score,
            "start_date": edu.start_date,
            "end_date": edu.end_date,
            "location": edu.location,
        })
    import json
    return json.dumps(edu_data, indent=2)
