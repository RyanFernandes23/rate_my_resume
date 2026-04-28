"""JD matcher prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate


BASE_JD_MATCHER_PROMPT = """You are a senior technical recruiter specialized in {tier} roles.
Your task is to compare a candidate's resume against a specific Job Description (JD).

{tier_specific_guidance}

Look for:
1. Tech Stack Alignment: Exact technology matches vs. adjacent ones.
2. Experience Depth: Does the candidate have the required seniority for this specific {tier} JD?
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
{{{{
    "match_score": number (0-100),
    "compatible_roles": ["Roles from the JD that the candidate fits"],
    "missing_critical_skills": ["Must-have skills from JD NOT in resume"],
    "missing_nice_to_have": ["Bonus skills from JD NOT in resume"],
    "tailoring_recommendations": [
        "Specific advice: 'The JD emphasizes AWS Lambda, but you only mentioned EC2 - highlight any serverless experience you have'",
        "Specific advice: 'This is a Senior role requiring mentorship, but your resume is purely individual contributor - add details on coaching juniors if applicable'"
    ]
}}}}

JOB DESCRIPTION:
{jd}

RESUME SUMMARY:
Name: {name}
Skills: {skills}
Experience: {experience}
Professional Summary: {professional_summary}

Return a JSON object with the JD matching analysis."""

STANDARD_GUIDANCE = """- Focus on overall professional alignment and core competency matches.
- Ensure the candidate meets the baseline requirements for a stable corporate/enterprise role."""

BIG_TECH_GUIDANCE = """Adapt JD matching based on the candidate's domain. Evaluate alignment with the target role:

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

STARTUP_GUIDANCE = """Match based on startup-relevant skills and mindset across domains:

TECHNOLOGY & ENGINEERING:
- Focus on versatility and "builder" mindset.
- Prioritize matches where the candidate has taken ownership of entire features or products from 0 to 1.
- Look for full-stack skills, rapid learning, and end-to-end ownership.

FINANCE & STARTUPS:
- Focus on adaptability and financial startup experience.
- Look for understanding of startup metrics, fundraising, or fintech backgrounds.
- Prioritize candidates comfortable with ambiguity and fast-paced environments.

CONSULTING & PROFESSIONAL SERVICES:
- Focus on rapid skill application and client versatility.
- Look for experience with diverse clients or fast project turnarounds.
- Prioritize problem-solving agility and communication skills.

PRODUCT MANAGEMENT:
- Focus on product ownership and speed to market.
- Look for end-to-end feature launches, user research, and metrics.
- Prioritize candidates who ship fast and iterate based on feedback.

MARKETING & GROWTH:
- Focus on multi-channel execution and growth mindset.
- Look for hands-on experience with campaigns, content, and analytics.
- Prioritize candidates who achieve measurable results quickly.

DATA SCIENCE & ML:
- Focus on end-to-end ML and quick prototyping.
- Look for model deployment, business impact, and rapid iteration.
- Prioritize candidates who connect ML to business value fast.

SALES & BUSINESS DEVELOPMENT:
- Focus on pipeline generation and Adaptability.
- Look for quota achievement, new business development, and relationship building.
- Prioritize hunters who thrive in fast-changing environments.

OPERATIONS & ADMIN:
- Focus on process building and resourcefulness.
- Look for multi-tasking, automation, and scaling experience.
- Prioritize candidates who do more with less.

Provide domain-specific matching scores highlighting startup-relevant skills."""

QUANT_GUIDANCE = """- Focus on technical precision and performance.
- Look for matches in low-level optimizations, algorithmic complexity, and mathematical rigor required by the JD."""

TIER_TEMPLATES = {
    "STANDARD": BASE_JD_MATCHER_PROMPT.format(tier="STANDARD", tier_specific_guidance=STANDARD_GUIDANCE, jd="{jd}", name="{name}", skills="{skills}", experience="{experience}", professional_summary="{professional_summary}"),
    "BIG_TECH": BASE_JD_MATCHER_PROMPT.format(tier="BIG TECH FANG", tier_specific_guidance=BIG_TECH_GUIDANCE, jd="{jd}", name="{name}", skills="{skills}", experience="{experience}", professional_summary="{professional_summary}"),
    "STARTUP": BASE_JD_MATCHER_PROMPT.format(tier="STARTUP", tier_specific_guidance=STARTUP_GUIDANCE, jd="{jd}", name="{name}", skills="{skills}", experience="{experience}", professional_summary="{professional_summary}"),
    "QUANT": BASE_JD_MATCHER_PROMPT.format(tier="QUANT", tier_specific_guidance=QUANT_GUIDANCE, jd="{jd}", name="{name}", skills="{skills}", experience="{experience}", professional_summary="{professional_summary}"),
}


def get_jd_matcher_prompt(tier: str = "STANDARD") -> ChatPromptTemplate:
    """Get the JD matching prompt for a specific tier."""
    tier_context = tier.upper().replace(" ", "_")
    template = TIER_TEMPLATES.get(tier_context, TIER_TEMPLATES["STANDARD"])
    return ChatPromptTemplate.from_template(template)


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
