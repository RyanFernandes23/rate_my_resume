import json
import logging
import os
from .schema import Resume
from .utils import parse_llm_json
from .protocol import LLMClient

logger = logging.getLogger(__name__)


def create_llm_client(model: str = None) -> LLMClient:
    from .adapters.retrying import RetryingLLMClient

    mode = os.getenv("LLM_MODE", "groq").lower()
    if mode == "openrouter":
        from .adapters.openrouter import OpenRouterAdapter
        inner = OpenRouterAdapter(model=model)
    elif mode == "cloudflare":
        from .adapters.cloudflare import CloudflareAdapter
        inner = CloudflareAdapter(model=model)
    else:
        from .adapters.groq import GroqAdapter
        inner = GroqAdapter(model=model)
    return RetryingLLMClient(inner)


def _normalize_data(data: dict) -> dict:
    fields_to_normalize = [
        "skills", "links", "experience", "education", "projects",
        "achievements", "certifications", "hobbies", "extra_curricular",
    ]
    for field in fields_to_normalize:
        if data.get(field) is None:
            data[field] = []

    if data.get("professional_summary") is None and data.get("summary"):
        data["professional_summary"] = data["summary"]
    elif data.get("summary") is None and data.get("professional_summary"):
        data["summary"] = data["professional_summary"]
    if data.get("total_years_experience") is None:
        data["total_years_experience"] = None
    if "experience" in data and data["experience"]:
        for exp in data["experience"]:
            if exp.get("descriptions") is None:
                exp["descriptions"] = []
    if "education" in data and data["education"]:
        for edu in data["education"]:
            for f in ("score", "location", "start_date", "end_date"):
                if edu.get(f) is None:
                    edu[f] = None
    if "projects" in data and data["projects"]:
        for proj in data["projects"]:
            if proj.get("descriptions") is None:
                proj["descriptions"] = []
            if proj.get("link") is None:
                proj["link"] = None
            proj.pop("technologies", None)
            proj.pop("description", None)
    if "achievements" in data and data["achievements"]:
        for ach in data["achievements"]:
            if ach.get("descriptions") is None:
                ach["descriptions"] = []
    if "certifications" in data and data["certifications"]:
        for cert in data["certifications"]:
            for f in ("issuer", "date", "link"):
                if cert.get(f) is None:
                    cert[f] = None
    return data


SYSTEM_PROMPT = """You are a resume parser. Extract structured information from the provided resume markdown.

Return a valid JSON object with these exact fields:
- name (string or null)
- email (string or null)
- phone (string or null)
- linkedin (string or null)
- github (string or null)
- location (string or null)
- professional_summary (string or null) - Also known as career summary, career objective, about me, profile summary
- summary (string or null) - Alias for professional_summary for backward compatibility
- links (array of URL strings)
- experience (array of objects with: company, title, start_date, end_date, descriptions)
- total_years_experience (number or null)
- education (array of objects with: name, score, start_date, end_date, location)
- skills (array of strings)
- projects (array of objects with: name, descriptions, link)
- achievements (array of objects with: title, descriptions)
- certifications (array of objects with: name, issuer, date, link)
- hobbies (array of strings)
- extra_curricular (array of strings)

Field-by-field requirements:
- name: full name as string
- email: email address as string
- phone: phone number as string
- linkedin: full LinkedIn URL as string
- github: full GitHub URL as string
- location: city, state/country as string
- summary: 2-3 sentence professional summary
- links: array of any additional URLs found
- experience[].company: company name
- experience[].title: job title
- experience[].start_date: start date (e.g., "July 2025" or "2025-07")
- experience[].end_date: end date or "Present"
- experience[].descriptions: ARRAY of strings, ONE string per bullet point
- total_years_experience: calculate years from all experience entries (e.g., 2.5)
- education[].name: institution/university name
- education[].score: GPA, percentage, or grade (e.g., "8.5 CGPA", "75%")
- education[].start_date: start year
- education[].end_date: end year or "Present"
- education[].location: city, state/country of institution
- skills: ARRAY of strings, each skill as separate item
- projects[].name: project title
- projects[].descriptions: ARRAY of strings, ONE string per bullet point
- projects[].link: project URL if available (can be null)
- achievements[].title: achievement title or description
- achievements[].descriptions: ARRAY of strings with details (can be empty if not available)
- certifications[].name: certification name
- certifications[].issuer: issuing organization (can be null if not available)
- certifications[].date: date obtained (can be null if not available)
- certifications[].link: URL to certification (can be null if not available)
- hobbies: ARRAY of strings, list personal hobbies/interests (empty if not available)
- extra_curricular: ARRAY of strings, volunteer work, clubs, activities (empty if not available)

IMPORTANT:
- For descriptions in experience and projects, each bullet point MUST be a separate string in the array
- If achievements section not present in resume, use empty array []
- If certifications section not present in resume, use empty array []
- If hobbies or extra_curricular not present, use empty array []
- If a field is not available, use null for strings and empty array [] for lists
- Return ONLY valid JSON, no other text"""

PROMPT_TEMPLATE = """{system_prompt}

Resume:
{resume}"""


async def extract_resume(markdown: str, llm_client: LLMClient) -> Resume:
    prompt = PROMPT_TEMPLATE.format(system_prompt=SYSTEM_PROMPT, resume=markdown)
    try:
        response = await llm_client.ainvoke(prompt)
        data = parse_llm_json(response)
        data = _normalize_data(data)
        return Resume(**data)
    except Exception as e:
        logger.error(f"Failed to extract resume: {str(e)}")
        if hasattr(e, "doc"):
            logger.error(f"Raw content was: {getattr(e, 'doc')[:200]}...")
        raise ValueError(f"Failed to extract resume: {str(e)}")
