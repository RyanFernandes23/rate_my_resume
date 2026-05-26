"""Certifications analyzer prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate

BASE_CERTIFICATIONS_PROMPT = """You are a senior recruiter specialized in professional enterprise roles. Analyze the certifications section below with production-grade enterprise expectations in mind.

SCORING_RUBRIC:
- 0-1 (POOR): Irrelevant or low-quality certification from unknown issuer. No evidence the knowledge was applied.
- 2-3 (AVERAGE): Recognized certification but from a lower-tier provider or missing details.
- 4 (STRONG): Industry-recognized certification (e.g., AWS, Google, Microsoft, CFA) with proper details, or a lesser cert with evidence of applied knowledge.
- 5 (EXPERT): High-impact, advanced certification from a top-tier provider with all details present and evidence of practical application.

Analyze each certification entry:
1. Check if organization/issuer name is valid and respected in professional enterprise roles.
2. Validate dates if provided.
3. Check if link is provided and valid format.
4. Determine if certification is relevant to a professional enterprise career path.
5. Assign a score from 0-5 based on the scoring rubric above.

For each certification, return a JSON object with:
{{
    "index": 0,
    "score": A score from 0-5 based on enterprise standards.,
    "name": "Certification Name",
    "is_valid": true/false,
    "organization_issues": ["issue1", "issue2"],
    "date_issues": ["issue1", "issue2"],
    "link_issues": ["issue1", "issue2"],
    "suggestions": ["Specific feedback about this certification (e.g., 'This AWS cert is valuable for enterprise roles. Consider adding a cloud-focused specialty like Solutions Architect Associate to strengthen your profile.')"]
}}
{{
    "index": 0,
    "name": "Certification Name",
    "is_valid": true/false,
    "organization_issues": ["issue1", "issue2"],
    "date_issues": ["issue1", "issue2"],
    "link_issues": ["issue1", "issue2"],
    "suggestions": ["Specific feedback about this certification (e.g., 'This AWS cert is valuable for enterprise roles. Consider adding a cloud-focused specialty like Solutions Architect Associate to strengthen your profile.')"]
}}

Certifications Data:
{{certifications_data}}

Return a JSON array of analysis objects for each certification."""


def get_certifications_prompt(tier: str = None) -> ChatPromptTemplate:
    """Get the certifications analysis prompt."""
    return ChatPromptTemplate.from_template(BASE_CERTIFICATIONS_PROMPT)


def format_certifications_data(certifications):
    """Format certification entries for the LLM prompt."""
    cert_data = []
    for i, cert in enumerate(certifications):
        cert_data.append({
            "index": i,
            "name": cert.name,
            "issuer": cert.issuer,
            "date": cert.date,
            "link": cert.link,
        })
    import json
    return json.dumps(cert_data, indent=2)
