"""Job role suggester prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate


BASE_JOB_ROLE_PROMPT = """You are a senior career advisor specialized in {tier} recruiting.

Based on the resume data below, suggest suitable job roles specifically within the {tier} ecosystem.

{tier_specific_guidance}

For each suggested role, return a JSON object with:
{{{{
    "role": "Job Role Title",
    "match_score": number (0-10),
    "reasoning": "Why this role fits based on skills/experience within the {tier} context",
    "suggestions": ["How to tailor resume specifically for this {tier} role"]
}}}}

Resume Data:
Skills: {skills}

Experience ({total_years} years):
{experience}

Projects:
{projects}

Return a JSON array of at least 5 job role suggestions sorted by match score (highest first)."""

STANDARD_GUIDANCE = """- Focus on mainstream software engineering roles (Full Stack, Backend, Frontend).
- Suggest roles that match standard enterprise tech stacks.
- Consider both individual contributor and early management roles if experience allows."""

BIG_TECH_GUIDANCE = """Suggest job roles based on the candidate's domain and experience level:

TECHNOLOGY & ENGINEERING:
- Focus on specialized roles common in large-scale tech (SRE, Infrastructure, Machine Learning, Distributed Systems).
- Suggest level-appropriate titles (e.g., Senior SWE for 5+ years, Staff for 10+).
- Prioritize roles requiring deep expertise in high-scale systems, cloud architecture, or platform engineering.

FINANCE & BANKING:
- Suggest roles like: Investment Analyst, Financial Analyst, Trading Analyst, Portfolio Manager, Risk Analyst, Quant Developer.
- Match level to experience: Associate (2-4 yrs), VP (5-8 yrs), Director (8-12 yrs).
- Consider both front-office (trading, IB) and back-office (risk, operations) roles.

CONSULTING:
- Suggest roles like: Management Consultant, Strategy Consultant, Business Analyst, Implementation Consultant.
- Match level to experience: Analyst (0-2 yrs), Consultant (2-4 yrs), Senior Consultant/Manager (4-7 yrs), Principal (7+ yrs).
- Consider both generalist and specialist (tech, healthcare, finance) tracks.

PRODUCT MANAGEMENT:
- Suggest roles like: Associate PM, Product Manager, Senior PM, Group PM, Director of Product.
- Match level to experience and industry background.
- Consider both B2B and B2C product paths.

MARKETING & GROWTH:
- Suggest roles like: Digital Marketing Manager, Growth Marketing Lead, Performance Marketing, Content Marketing Manager, Brand Manager.
- Match level to experience and channel expertise.
- Consider both in-house and agency paths.

DATA SCIENCE & ML:
- Suggest roles like: Data Analyst, Data Scientist, ML Engineer, Senior Data Scientist, Research Scientist, AI Engineer.
- Match level to ML complexity and business impact.
- Consider both individual contributor and lead/manager paths for senior roles.

SALES & BUSINESS DEVELOPMENT:
- Suggest roles like: Sales Representative, Account Executive, Senior AE, Enterprise Account Executive, Sales Manager, Business Development Manager.
- Match level to deal size and team management responsibilities.
- Consider both SMB and enterprise tracks.

OPERATIONS & SUPPLY CHAIN:
- Suggest roles like: Operations Analyst, Supply Chain Analyst, Logistics Manager, Operations Manager, Procurement Manager.
- Match level to scope and team size.
- Consider both manufacturing and service operations.

Provide at least 5 role suggestions sorted by match score (highest first), with clear reasoning for each."""

STARTUP_GUIDANCE = """Suggest job roles that match high-ownership, fast-paced startup environments across domains:

TECHNOLOGY & ENGINEERING:
- Focus on high-ownership roles (Founding Engineer, Lead Full-Stack, Product-Focused Engineer).
- Suggest roles requiring versatility and fast-paced execution.
- Prioritize roles involving building from 0-to-1.
- Match level: Early (Junior/Mid) to Principal/Founding roles based on experience.

FINANCE & STARTUPS:
- Suggest roles in fintech, financial services startups, or venture-backed finance.
- Match to experience: Associate (2-4 yrs), Manager (4-7 yrs), Director (7+ yrs).
- Consider: FP&A, corporate finance, investor relations, or fintech product roles.
- Value: Adaptability, startup mindset, and financial acumen.

CONSULTING & PROFESSIONAL SERVICES:
- Suggest roles in boutique consultancies or advisory startups.
- Match to experience: Analyst (0-2 yrs), Consultant (2-4 yrs), Manager (4-7 yrs).
- Consider: Strategy, operations, or specialized consulting roles.
- Value: Rapid learning, client-facing skills, versatility.

PRODUCT MANAGEMENT:
- Suggest PM roles at early or growth-stage startups.
- Match to experience: Associate PM (0-2 yrs), PM (2-5 yrs), Senior PM (5-8 yrs), Group PM (8+ yrs).
- Consider: B2B, B2C, or platform product roles.
- Value: End-to-end ownership, speed, metrics-driven.

MARKETING & GROWTH:
- Suggest roles in growth-stage startups or digital agencies.
- Match to experience: Coordinator (0-2 yrs), Manager (2-4 yrs), Lead (4-7 yrs), Director (7+ yrs).
- Consider: Digital marketing, growth, content, or brand roles.
- Value: Hands-on execution, measurable results, multi-channel expertise.

DATA SCIENCE & ML:
- Suggest roles in AI/ML startups or data-driven companies.
- Match to experience: Junior DS (0-2 yrs), DS (2-4 yrs), Senior DS (4-7 yrs), Lead/Staff (7+ yrs).
- Consider: Applied ML, data engineering, or research roles.
- Value: End-to-end ML, business impact, rapid prototyping.

SALES & BUSINESS DEVELOPMENT:
- Suggest roles in startups building sales teams from scratch.
- Match to experience: Rep (0-2 yrs), AE (2-4 yrs), Senior AE (4-7 yrs), Manager/Director (7+ yrs).
- Consider: SMB, mid-market, or enterprise tracks.
- Value: Hunter mentality, pipeline generation, Adaptability.

OPERATIONS & ADMIN:
- Suggest ops roles at scaling startups.
- Match to experience: Coordinator (0-2 yrs), Manager (2-4 yrs), Senior Manager (4-7 yrs), Director (7+ yrs).
- Consider: People ops, finance ops, or general ops roles.
- Value: Multi-tasking, process building, resourcefulness.

Provide at least 5 role suggestions sorted by match score, with clear reasoning for startup fit."""

QUANT_GUIDANCE = """- Focus on highly technical and mathematical roles (Quantitative Developer, FPGA Engineer, Low-Latency C++ Dev).
- Suggest roles that prioritize performance and precision over breadth.
- Prioritize roles in high-frequency trading or algorithmic research."""

TIER_TEMPLATES = {
    "STANDARD": BASE_JOB_ROLE_PROMPT.format(tier="STANDARD", tier_specific_guidance=STANDARD_GUIDANCE, skills="{skills}", total_years="{total_years}", experience="{experience}", projects="{projects}"),
    "BIG_TECH": BASE_JOB_ROLE_PROMPT.format(tier="BIG TECH FANG", tier_specific_guidance=BIG_TECH_GUIDANCE, skills="{skills}", total_years="{total_years}", experience="{experience}", projects="{projects}"),
    "STARTUP": BASE_JOB_ROLE_PROMPT.format(tier="STARTUP", tier_specific_guidance=STARTUP_GUIDANCE, skills="{skills}", total_years="{total_years}", experience="{experience}", projects="{projects}"),
    "QUANT": BASE_JOB_ROLE_PROMPT.format(tier="QUANT", tier_specific_guidance=QUANT_GUIDANCE, skills="{skills}", total_years="{total_years}", experience="{experience}", projects="{projects}"),
}


def get_job_role_prompt(tier: str = "STANDARD") -> ChatPromptTemplate:
    """Get the job role suggestion prompt for a specific tier."""
    tier_context = tier.upper().replace(" ", "_")
    template = TIER_TEMPLATES.get(tier_context, TIER_TEMPLATES["STANDARD"])
    return ChatPromptTemplate.from_template(template)


def format_job_role_data(skills, experience, projects, total_years):
    """Format job role data for the LLM prompt."""
    import json
    return {
        "skills": json.dumps(skills or [], indent=2),
        "experience": json.dumps(experience or [], indent=2),
        "projects": json.dumps(projects or [], indent=2),
        "total_years": total_years,
    }
