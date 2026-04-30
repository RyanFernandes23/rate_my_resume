"""Certifications analyzer using LangChain and externalized prompts."""
import json
from ..llm.client import llm
from ..analyzer.schemas import CertificationAnalysis
from .prompts.certifications_prompts import get_certifications_prompt, format_certifications_data


def analyze_certifications(resume):
    """Analyze all certification entries using LLM with externalized prompts."""
    if not resume.certifications:
        return []

    # Use LangChain prompt template
    prompt = get_certifications_prompt()
    formatted_prompt = prompt.format(
        certifications_data=format_certifications_data(resume.certifications),
    )

    try:
        response = llm.invoke(formatted_prompt)
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
        return _fallback_certifications_analysis(resume.certifications, e)


def _fallback_certifications_analysis(certifications, error):
    """Fallback analysis when LLM fails."""
    result = []
    for i, cert in enumerate(certifications):
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
