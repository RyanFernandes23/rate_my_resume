"""Consolidator prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate


BASE_CONSOLIDATOR_PROMPT = """You are a senior recruitment strategist specialized in {tier} roles. Your task is to provide a final assessment of the candidate based on their resume analysis results.

{tier_specific_guidance}

Create a final JSON output with:
1. Overall Summary - A direct, no-nonsense conversational 3-4 sentence assessment of the candidate's fit for {tier} roles. BE HONEST and CRITICAL. If the resume is weak, say so directly (e.g., 'Hey, honestly, this resume is quite weak for {tier} right now. You're missing critical impact metrics and the technical depth isn't coming through. You need a major overhaul to be competitive.').
2. Strengths - list of 3-5 key strengths specifically valuable for {tier}.
3. Areas for Improvement - list of 3-5 key improvements needed to meet {tier} standards.

STRICTNESS RULES:
- If the benchmark grade is C or lower, the summary MUST be highly critical.
- Do not use generic praise unless it is truly deserved.
- For {tier}, emphasize the biggest gap found in the scores.

Analysis Data:
{analysis_summary}

Return a JSON object with:
{{{{
    "overall_summary": "...",
    "strengths": ["...", "..."],
    "areas_for_improvement": ["...", "..."]
}}}}"""

STANDARD_GUIDANCE = """- Assess fit for general software engineering roles.
- Focus on professional communication, clear results, and breadth of technical skills."""

BIG_TECH_GUIDANCE = """Assess fit based on the candidate's domain. Adapt evaluation to the relevant field:

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

Provide domain-specific feedback that helps the candidate understand their fit for their target field."""

STARTUP_GUIDANCE = """Assess fit for startup environments based on the candidate's domain:

TECHNOLOGY & ENGINEERING:
- Assess fit for fast-paced, high-ownership startup environments.
- Focus on versatility, 0-to-1 building experience, and speed of execution.
- Evaluate ability to work across stack, ship fast, and own products end-to-end.

FINANCE & STARTUPS:
- Assess fit for fintech, financial services startups, or venture-backed companies.
- Focus on adaptability, financial acumen, and comfort with ambiguity.
- Evaluate understanding of startup metrics (MRR, ARR, runway) and growth.

CONSULTING & PROFESSIONAL SERVICES:
- Assess fit for boutique consultancies or advisory startups.
- Focus on client-facing skills, rapid problem-solving, and versatility.
- Evaluate ability to work with multiple industries and deliver fast.

PRODUCT MANAGEMENT:
- Assess fit for product roles at early-stage startups or growth-stage companies.
- Focus on end-to-end product ownership, speed, and user-centric thinking.
- Evaluate metrics-driven decision making and cross-functional leadership.

MARKETING & GROWTH:
- Assess fit for growth-stage startups or digital agencies.
- Focus on execution speed, multi-channel expertise, and measurable results.
- Evaluate hands-on approach and comfort with limited resources.

DATA SCIENCE & ML:
- Assess fit for AI/ML startups or data-driven companies.
- Focus on end-to-end model development and business impact.
- Evaluate ability to move fast with limited infrastructure.

SALES & BUSINESS DEVELOPMENT:
- Assess fit for startups building sales teams from scratch.
- Focus on pipeline generation, adaptability, and hunter mentality.
- Evaluate comfort with fast-changing priorities and direct revenue impact.

OPERATIONS & ADMIN:
- Assess fit for ops roles at scaling startups.
- Focus on multi-tasking, process building, and resourcefulness.
- Evaluate ability to build systems with limited resources.

Provide domain-specific feedback on startup readiness and fit."""

QUANT_GUIDANCE = """- Assess fit for extremely technical and mathematically rigorous environments.
- Focus on algorithmic efficiency, low-level optimization, and mathematical precision."""

TIER_TEMPLATES = {
    "STANDARD": BASE_CONSOLIDATOR_PROMPT.format(tier="STANDARD", tier_specific_guidance=STANDARD_GUIDANCE, analysis_summary="{analysis_summary}"),
    "BIG_TECH": BASE_CONSOLIDATOR_PROMPT.format(tier="BIG TECH FANG", tier_specific_guidance=BIG_TECH_GUIDANCE, analysis_summary="{analysis_summary}"),
    "STARTUP": BASE_CONSOLIDATOR_PROMPT.format(tier="STARTUP", tier_specific_guidance=STARTUP_GUIDANCE, analysis_summary="{analysis_summary}"),
    "QUANT": BASE_CONSOLIDATOR_PROMPT.format(tier="QUANT", tier_specific_guidance=QUANT_GUIDANCE, analysis_summary="{analysis_summary}"),
}


def get_consolidator_prompt(tier: str = "STANDARD") -> ChatPromptTemplate:
    """Get the consolidation prompt for a specific tier."""
    tier_context = tier.upper().replace(" ", "_")
    template = TIER_TEMPLATES.get(tier_context, TIER_TEMPLATES["STANDARD"])
    return ChatPromptTemplate.from_template(template)


def format_consolidator_data(
    basic_info_score,
    experience_score,
    projects_score,
    skills_score,
    education_score,
    achievements_hobbies_score,
    certifications_score,
    job_role_suggestions,
    target_tier,
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
        "target_tier": target_tier,
        "benchmark_grade": benchmark_grade,
    }
    return {"analysis_summary": json.dumps(summary_data, indent=2)}
