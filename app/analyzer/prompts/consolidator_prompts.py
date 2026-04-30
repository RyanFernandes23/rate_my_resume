"""Consolidator prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate


BASE_CONSOLIDATOR_PROMPT = """You are a senior recruitment strategist. Your task is to provide a final assessment of the candidate based on their resume analysis results with high-standard enterprise expectations.

RECRUITER GUIDANCE:
Assess fit based on the candidate's domain. Adapt evaluation to the relevant field:

TECHNOLOGY & ENGINEERING:
- Assess fit for high-scale, high-reliability engineering environments.
- Focus on technical depth, system design capabilities, and quantifiable impact on large-scale systems.
- Evaluate distributed systems knowledge, cloud infrastructure, and operational excellence.

FINANCE & BANKING:
- Assess fit for investment banking, trading, or financial technology roles.
- Focus on quantitative skills, financial modeling, and regulatory knowledge.
- Evaluate deal experience, risk management, and client-facing capabilities.

CONSULTING:
- Assess fit for top-tier consulting firms (McKinsey, BCG, Bain, or specialist consultancies).
- Focus on problem-solving frameworks, client communication, and strategic thinking.
- Evaluate industry expertise, stakeholder management, and delivery excellence.

PRODUCT MANAGEMENT:
- Assess fit for product management roles at tech companies or startups.
- Focus on product strategy, metrics-driven decision making, and user-centric design.
- Evaluate cross-functional leadership and roadmap ownership.

MARKETING & GROWTH:
- Assess fit for digital marketing, growth, or brand roles.
- Focus on channel expertise, campaign performance, and analytical abilities.
- Evaluate creativity, data-driven decision making, and growth experimentation.

DATA SCIENCE & ML:
- Assess fit for data science, machine learning, or AI roles.
- Focus on model development, statistical rigor, and production deployment.
- Evaluate end-to-end ML lifecycle experience and business impact.

SALES & BUSINESS DEVELOPMENT:
- Assess fit for enterprise sales or business development roles.
- Focus on quota achievement, pipeline generation, and relationship building.
- Evaluate negotiation skills, territory development, and revenue impact.

OPERATIONS & SUPPLY CHAIN:
- Assess fit for operations, supply chain, or logistics roles.
- Focus on process optimization, vendor management, and scaling operations.
- Evaluate Lean/Six Sigma, ERP systems, and operational metrics.

Create a final JSON output with:
1. Overall Summary - A direct, no-nonsense conversational 3-4 sentence assessment of the candidate's fit. BE HONEST and CRITICAL. If the resume is weak, say so directly.
2. Strengths - list of 3-5 key strengths valuable for professional enterprise roles.
3. Areas for Improvement - list of 3-5 key improvements needed to meet high professional standards.

STRICTNESS RULES:
- If the benchmark grade is C or lower, the summary MUST be highly critical.
- Do not use generic praise unless it is truly deserved.
- Emphasize the biggest gap found in the scores.

Analysis Data:
{analysis_summary}

Return a JSON object with:
{{
    "overall_summary": "...",
    "strengths": ["...", "..."],
    "areas_for_improvement": ["...", "..."]
}}"""


def get_consolidator_prompt() -> ChatPromptTemplate:
    """Get the consolidation prompt."""
    return ChatPromptTemplate.from_template(BASE_CONSOLIDATOR_PROMPT)


def format_consolidator_data(
    basic_info_score,
    experience_score,
    projects_score,
    skills_score,
    education_score,
    achievements_hobbies_score,
    certifications_score,
    job_role_suggestions,
    benchmark_grade,
):
    """Format consolidation data for the LLM prompt."""
    import json
    summary_data = {
        "basic_info_score": basic_info_score,
        "experience_score": experience_score,
        "projects_score": projects_score,
        "skills_score": skills_score,
        "education_score": education_score,
        "achievements_hobbies_score": achievements_hobbies_score,
        "certifications_score": certifications_score,
        "job_role_suggestions": [r.role for r in job_role_suggestions[:3]] if job_role_suggestions else [],
        "benchmark_grade": benchmark_grade,
    }
    return {"analysis_summary": json.dumps(summary_data, indent=2)}
