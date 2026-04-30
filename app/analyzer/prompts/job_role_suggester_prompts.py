"""Job role suggester prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate

ENTERPRISE_GUIDANCE = """Suggest job roles based on the candidate's domain and experience level with professional enterprise standards:

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

BASE_JOB_ROLE_PROMPT = """You are a senior career advisor specialized in professional enterprise recruiting.

Based on the resume data below, suggest suitable job roles specifically within the professional enterprise ecosystem.

Suggest job roles based on the candidate's domain and experience level with professional enterprise standards:

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

Provide at least 5 role suggestions sorted by match score (highest first), with clear reasoning for each.

For each suggested role, return a JSON object with:
{{
    "role": "Job Role Title",
    "match_score": number (0-10),
    "reasoning": "Why this role fits based on skills/experience within the professional enterprise context",
    "suggestions": ["How to tailor resume specifically for this professional enterprise role"]
}}

Resume Data:
Skills: {{skills}}

Experience ({{total_years}} years):
{{experience}}

Projects:
{{projects}}

Return a JSON array of at least 5 job role suggestions sorted by match score (highest first)."""


def get_job_role_prompt(tier: str = None) -> ChatPromptTemplate:
    """Get the job role suggestion prompt."""
    return ChatPromptTemplate.from_template(BASE_JOB_ROLE_PROMPT)


def format_job_role_data(skills, experience, projects, total_years):
    """Format job role data for the LLM prompt."""
    import json
    return {
        "skills": json.dumps(skills or [], indent=2),
        "experience": json.dumps(experience or [], indent=2),
        "projects": json.dumps(projects or [], indent=2),
        "total_years": total_years,
    }
