"""JD matcher prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate

ENTERPRISE_GUIDANCE = """Adapt JD matching based on the candidate's domain with professional enterprise standards. Evaluate alignment with the target role:

TECHNOLOGY & ENGINEERING:
- Focus on engineering excellence at scale.
- Look for evidence of handling distributed systems, large data volumes, and high-availability requirements.
- Evaluate cloud platforms, system design, and operational experience.

FINANCE & BANKING:
- Focus on financial domain expertise and relevant certifications (CFA, CPA, FRM).
- Look for experience with financial modeling, risk management, or trading systems.
- Evaluate regulatory knowledge and compliance experience.

CONSULTING:
- Focus on strategic problem-solving and frameworks.
- Look for Fortune 500 client experience and case study examples.
- Evaluate presentation skills, stakeholder management, and industry expertise.

PRODUCT MANAGEMENT:
- Focus on product strategy and metrics-driven decision making.
- Look for experience with user research, A/B testing, and roadmap ownership.
- Evaluate cross-functional leadership and product launches.

MARKETING & GROWTH:
- Focus on digital marketing expertise and channel knowledge.
- Look for campaign management, analytics, and growth experimentation experience.
- Evaluate ROI/ROAS performance and audience targeting skills.

DATA SCIENCE & ML:
- Focus on ML/AI technical skills and production experience.
- Look for model development, deployment, and business impact.
- Evaluate Python, TensorFlow/PyTorch, and data engineering skills.

SALES & BUSINESS DEVELOPMENT:
- Focus on quota achievement and pipeline generation.
- Look for enterprise deal experience and relationship management.
- Evaluate CRM proficiency and negotiation skills.

OPERATIONS & SUPPLY CHAIN:
- Focus on process optimization and operational efficiency.
- Look for ERP experience, Lean/Six Sigma, and vendor management.
- Evaluate scaling operations and KPI management.

Provide domain-specific matching scores and gap analysis."""

BASE_JD_MATCHER_PROMPT = """You are a senior technical recruiter specialized in professional enterprise roles.
Your task is to compare a candidate's resume against a specific Job Description (JD).

Adapt JD matching based on the candidate's domain with professional enterprise standards. Evaluate alignment with the target role:

TECHNOLOGY & ENGINEERING:
- Focus on engineering excellence at scale.
- Look for evidence of handling distributed systems, large data volumes, and high-availability requirements.
- Evaluate cloud platforms, system design, and operational experience.

FINANCE & BANKING:
- Focus on financial domain expertise and relevant certifications (CFA, CPA, FRM).
- Look for experience with financial modeling, risk management, or trading systems.
- Evaluate regulatory knowledge and compliance experience.

CONSULTING:
- Focus on strategic problem-solving and frameworks.
- Look for Fortune 500 client experience and case study examples.
- Evaluate presentation skills, stakeholder management, and industry expertise.

PRODUCT MANAGEMENT:
- Focus on product strategy and metrics-driven decision making.
- Look for experience with user research, A/B testing, and roadmap ownership.
- Evaluate cross-functional leadership and product launches.

MARKETING & GROWTH:
- Focus on digital marketing expertise and channel knowledge.
- Look for campaign management, analytics, and growth experimentation experience.
- Evaluate ROI/ROAS performance and audience targeting skills.

DATA SCIENCE & ML:
- Focus on ML/AI technical skills and production experience.
- Look for model development, deployment, and business impact.
- Evaluate Python, TensorFlow/PyTorch, and data engineering skills.

SALES & BUSINESS DEVELOPMENT:
- Focus on quota achievement and pipeline generation.
- Look for enterprise deal experience and relationship management.
- Evaluate CRM proficiency and negotiation skills.

OPERATIONS & SUPPLY CHAIN:
- Focus on process optimization and operational efficiency.
- Look for ERP experience, Lean/Six Sigma, and vendor management.
- Evaluate scaling operations and KPI management.

Provide domain-specific matching scores and gap analysis.

Look for:
1. Tech Stack Alignment: Exact technology matches vs. adjacent ones.
2. Experience Depth: Does the candidate have the required seniority for this specific professional enterprise JD?
3. Domain Knowledge: Match between candidate projects and JD domain.
4. Impact Match: Are the JD's core responsibilities reflected in the candidate's achievements?

SCORING_RUBRIC (STRICT):
- 0-30 (POOR): Major skills gap. Seniority mismatch (e.g., Intern applying for Senior role).
- 31-60 (AVERAGE): Meets some requirements but lacks key technologies or relevant domain experience.
- 61-85 (STRONG): Meets all "must-have" requirements. Good tech stack and seniority alignment.
- 86-100 (EXPERT): Perfect match. Seniority exceeds JD requirements, or has identical domain experience with high impact.

STRICTNESS RULES:
- BE EXTREMELY CRITICAL. Most candidates should score between 40-70.
- PENALIZE HEAVILY if a "Must-have" skill from the JD is missing.
- If the JD asks for "Senior" and the resume shows "Junior", the score should NOT exceed 40.

Return a JSON object with:
{{
    "match_score": number (0-100),
    "compatible_roles": ["Roles from the JD that the candidate fits"],
    "missing_critical_skills": ["Must-have skills from JD NOT in resume"],
    "missing_nice_to_have": ["Bonus skills from JD NOT in resume"],
    "tailoring_recommendations": [
        "Specific advice: 'The JD emphasizes AWS Lambda, but you only mentioned EC2 - highlight any serverless experience you have'",
        "Specific advice: 'This is a Senior role requiring mentorship, but your resume is purely individual contributor - add details on coaching juniors if applicable'"
    ]
}}

JOB DESCRIPTION:
{{jd}}

RESUME SUMMARY:
Name: {{name}}
Skills: {{skills}}
Experience: {{experience}}
Professional Summary: {{professional_summary}}

Return a JSON object with the JD matching analysis."""


def get_jd_matcher_prompt(tier: str = None) -> ChatPromptTemplate:
    """Get the JD matching prompt."""
    return ChatPromptTemplate.from_template(BASE_JD_MATCHER_PROMPT)


def format_jd_data(jd, resume):
    """Format JD and resume data for the LLM prompt."""
    import json
    skills = resume.skills or []
    exp_titles = [f"{e.title} at {e.company}" for e in resume.experience or []]
    return {
        "jd": jd,
        "name": resume.name,
        "skills": json.dumps(skills),
        "experience": json.dumps(exp_titles),
        "professional_summary": resume.professional_summary or "None",
    }
