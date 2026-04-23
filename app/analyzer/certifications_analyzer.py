import json
from ..llm.client import llm
from .schemas import CertificationAnalysis


CERTIFICATIONS_ANALYZER_PROMPT = """You are a resume analysis expert specializing in certifications evaluation.

Analyze each certification entry:
1. Check if organization/issuer name is valid
2. Validate dates if provided
3. Check if link is provided and valid format
4. Determine if certification is relevant to career

For each certification, return a JSON object with:
{
    "index": 0,
    "name": "Certification Name",
    "is_valid": true/false,
    "organization_issues": ["issue1", "issue2"],
    "date_issues": ["issue1", "issue2"],
    "link_issues": ["issue1", "issue2"],
    "suggestions": ["suggestion1", "suggestion2"]
}

Validations:
- Organization should be a known entity (e.g., AWS, Google, Microsoft)
- Dates should not be in the future
- Links should be valid URLs (https://...)
- Expired certifications might need renewal mention

Analyze all certifications and return a JSON array of analysis objects."""


def analyze_certifications(resume) -> list[CertificationAnalysis]:
    """Analyze all certification entries"""

    if not resume.certifications:
        return []

    # Build certification data
    cert_data = []
    for i, cert in enumerate(resume.certifications):
        cert_data.append(
            {
                "index": i,
                "name": cert.name,
                "issuer": cert.issuer,
                "date": cert.date,
                "link": cert.link,
            }
        )

    prompt = f"""{CERTIFICATIONS_ANALYZER_PROMPT}

Certifications Data:
{json.dumps(cert_data, indent=2)}

Return a JSON array of analysis objects for each certification."""

    try:
        response = llm.invoke(prompt)
        json_str = response.content.strip()

        # Clean up markdown
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        elif json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()

        analyses = json.loads(json_str)

        # Convert to CertificationAnalysis objects with actual scoring
        result = []
        for analysis in analyses:
            # Calculate actual score based on data completeness: 5pts total per cert
            # Name (1pt) + issuer (1pt) + date (1pt) + link (1pt) + is_valid (1pt)
            score = 0.0
            cert = resume.certifications[analysis.get("index", 0)] if analysis.get("index", 0) < len(resume.certifications) else None
            
            if analysis.get("name") or (cert and cert.name):
                score += 1.0
            if analysis.get("is_valid", True):
                score += 1.0
            if not analysis.get("organization_issues"):
                score += 1.0
            if not analysis.get("date_issues"):
                score += 1.0
            if not analysis.get("link_issues") and (cert and cert.link):
                score += 1.0
            
            result.append(
                CertificationAnalysis(
                    index=analysis.get("index", 0),
                    name=analysis.get("name", "") or (cert.name if cert else ""),
                    is_valid=analysis.get("is_valid", True),
                    organization_issues=analysis.get("organization_issues", []),
                    date_issues=analysis.get("date_issues", []),
                    link_issues=analysis.get("link_issues", []),
                    suggestions=analysis.get("suggestions", []),
                    score=round(score, 2),
                )
            )

        return result

    except Exception as e:
        # Fallback with stricter scoring
        result = []
        for i, cert in enumerate(resume.certifications):
            # Calculate actual score
            score = 0.0
            
            if cert.name:
                score += 1.0  # Has name
            if cert.issuer:
                score += 1.0  # Has issuer
            if cert.date:
                score += 1.0  # Has date
            if cert.link:
                score += 1.0  # Has link
            score += 1.0  # Valid entry exists - assumes valid
            
            result.append(
                CertificationAnalysis(
                    index=i,
                    name=cert.name,
                    is_valid=True,
                    organization_issues=[],
                    date_issues=[],
                    link_issues=[],
                    suggestions=[],
                    score=round(score, 2),
                )
            )
        return result
