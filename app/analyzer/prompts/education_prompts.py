"""Education analyzer prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate


BASE_EDUCATION_PROMPT = """You are a senior recruiter specialized in {tier} roles. Analyze the education section below with {tier} expectations in mind.

Recruiter Perspective on Education for {tier}:
{tier_specific_guidance}

Experience Context: Total years of experience = {total_years} years
- If total_years >= 2: Generally suggest condensing education (university name + dates only).
- If total_years < 2: Suggest keeping degree + expected graduation + major details.

Analyze each education entry:
1. Check if institution name is valid and properly formatted.
2. Validate dates (start should be before end, should be recent).
3. Evaluate GPA/score - determine if it should be kept or removed based on {tier} standards.
4. Check for location information.
5. Apply experience-based logic to suggestions.

SCORING_RUBRIC (STRICT):
- 0-4 (POOR): Missing major/degree, unrecognizable institution, or incoherent dates.
- 5-7 (AVERAGE): Recognized university with complete details but average performance or relevance.
- 8-9 (STRONG): High GPA, relevant major/minors, and recognized institution.
- 10 (EXPERT): Top-tier/Elite institution (Ivy League, MIT, IIT, etc.) with exceptional honors or GPA.

STRICTNESS RULES:
- BE CRITICAL. If the university is non-accredited or extremely low rank, the score should stay below 6.
- Penalize missing GPA if the candidate is a fresh graduate (<2 years exp).
- For {tier}, check if the degree is highly relevant (e.g., CS, Math, Engineering).

For each education entry, return a JSON object with:
{{{{
    "entry_index": 0,
    "score": A score from 0-10 based on completeness and prestige (if {tier} requires it).,
    "institution_name_valid": true/false,
    "institution_name": "Institution Name",
    "date_issues": ["issue1", "issue2"],
    "gpa_analysis": {{{{
        "value": "8.5 CGPA" or null,
        "recommendation": "keep/remove",
        "reasoning": "explanation"
    }}}},
    "issues": [{{{{ "issue": "description", "severity": "high/medium/low", "reason": "explanation" }}}}],
    "suggestions": ["Specific feedback about this education entry (e.g., 'Your degree is relevant for {tier}. Consider adding coursework like Data Structures or Machine Learning to show technical depth in your field.')"]
}}}}

Education Data:
{education_data}

Return a JSON array of analysis objects for each education entry."""

STANDARD_GUIDANCE = """- Education is a baseline check.
- GPA recommendation: Keep if > 7.5 CGPA or > 70%. Remove if < 6.5.
- Normal duration: 3-4 years for Bachelor's, 2 for Master's."""

BIG_TECH_GUIDANCE = """Evaluate education based on the candidate's domain. Adapt criteria accordingly:

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

STARTUP_GUIDANCE = """Evaluate education based on practical skills and adaptability, not just prestige. Adapt based on domain:

TECHNOLOGY & ENGINEERING:
- Practical skills outweigh school prestige.
- GPA: Lower emphasis (Keep if > 7.0 CGPA or 3.0/4.0); focus on projects and internships.
- Look for: Coding bootcamps, self-taught skills, open source contributions, hackathons.
- Graduation Date: Speed of entering workforce matters more.

FINANCE & STARTUPS:
- Practical finance skills outweigh prestige.
- GPA: Keep if > 6.5 CGPA or 3.0/4.0; relevant internships matter more.
- Look for: Side projects, financial modeling clubs, startup involvement.
- Value: Quick learners who can adapt to fast-changing finance tech.

CONSULTING & PROFESSIONAL SERVICES:
- Client-facing skills and rapid learning matter more than school.
- GPA: Keep if > 6.5 CGPA or 3.0/4.0; case competition wins valued.
- Look for: Leadership in clubs, entrepreneurship, diverse interests.
- Value: Communication skills and business acumen over prestige.

PRODUCT MANAGEMENT:
- Product skills and mindset outweigh academic credentials.
- GPA: Flexible (Keep if > 6.0 CGPA or 2.8/4.0); focus on projects.
- Look for: Product clubs, side projects, user research experience.
- Value: User empathy, analytical thinking, communication.

MARKETING & GROWTH:
- Creative skills and results orientation matter most.
- GPA: Very flexible (Keep if > 6.0 CGPA or 2.5/4.0).
- Look for: Portfolio work, social media presence, marketing clubs.
- Value: Creativity, hands-on experience, results orientation.

DATA SCIENCE & ML:
- Practical ML skills and projects outweigh prestige.
- GPA: Keep if > 7.5 CGPA or 3.2/4.0; Kaggle, projects matter more.
- Look for: Personal ML projects, open source, research.
- Value: Practical skills and ability to deliver fast.

SALES & BUSINESS DEVELOPMENT:
- Track record and interpersonal skills outweigh education.
- GPA: Very flexible (Keep if > 6.0 CGPA or 2.5/4.0).
- Look for: Sales clubs, leadership, networking, entrepreneurship.
- Value: Communication, persistence, relationship building.

OPERATIONS & ADMIN:
- Practical ops skills and adaptability matter most.
- GPA: Keep if > 6.5 CGPA or 3.0/4.0.
- Look for: Leadership, clubs, practical projects.
- Value: Multi-tasking, problem-solving, resourcefulness.

Focus on practical skills, projects, and adaptability over academic prestige. Graduation speed is valued."""

QUANT_GUIDANCE = """- Extreme emphasis on University Prestige and Mathematical Rigor.
- GPA recommendation: Elite standards (Keep only if > 9.0 CGPA or Top 5% of class).
- Focus on: Math, Physics, or CS degrees from top-tier institutions."""

TIER_TEMPLATES = {
    "STANDARD": BASE_EDUCATION_PROMPT.format(tier="STANDARD", tier_specific_guidance=STANDARD_GUIDANCE, total_years="{total_years}", education_data="{education_data}"),
    "BIG_TECH": BASE_EDUCATION_PROMPT.format(tier="BIG TECH FANG", tier_specific_guidance=BIG_TECH_GUIDANCE, total_years="{total_years}", education_data="{education_data}"),
    "STARTUP": BASE_EDUCATION_PROMPT.format(tier="STARTUP", tier_specific_guidance=STARTUP_GUIDANCE, total_years="{total_years}", education_data="{education_data}"),
    "QUANT": BASE_EDUCATION_PROMPT.format(tier="QUANT", tier_specific_guidance=QUANT_GUIDANCE, total_years="{total_years}", education_data="{education_data}"),
}


def get_education_prompt(tier: str = "STANDARD") -> ChatPromptTemplate:
    """Get the education analysis prompt for a specific tier."""
    tier_context = tier.upper().replace(" ", "_")
    template = TIER_TEMPLATES.get(tier_context, TIER_TEMPLATES["STANDARD"])
    return ChatPromptTemplate.from_template(template)


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
