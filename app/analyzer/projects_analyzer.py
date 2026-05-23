"""Projects analyzer using LangChain and externalized prompts."""
import json
from typing import Optional
from ..llm.protocol import LLMClient
from ..llm.utils import parse_llm_json
from ..analyzer.schemas import ProjectsAnalysis, AnalysisIssue, BulletSuggestion
from .prompts.projects_prompts import get_projects_prompt, format_projects_data


def _clean_suggestion(suggestion: str) -> str:
    """Remove redundant preambles from suggestion strings."""
    phrases_to_remove = [
        "add this to demonstrate impact",
        "add this to show",
        "demonstrate impact by",
    ]
    suggestion_lower = suggestion.lower().strip()
    for phrase in phrases_to_remove:
        if suggestion_lower.startswith(phrase):
            suggestion = suggestion[len(phrase):].strip()
            if suggestion and not suggestion[0].isupper():
                suggestion = suggestion[0].upper() + suggestion[1:]
            break
    return suggestion


async def analyze_projects(resume, llm_client: LLMClient):
    """Analyze all project entries using LLM with externalized prompts."""
    from ..analyzer.schemas import ProjectsAnalysis

    if not resume.projects:
        return []

    # Use LangChain prompt template
    prompt = get_projects_prompt()
    formatted_prompt = prompt.format(
        projects_data=format_projects_data(resume.projects),
    )

    try:
        response = await llm_client.ainvoke(formatted_prompt)
        analysis_data = parse_llm_json(response)
        entries_data = analysis_data.get("entries", [])

        result = []
        for i, proj in enumerate(resume.projects):
            # Find entry in LLM response or use default
            entry_data = next((e for e in entries_data if e.get("entry_index") == i), {})
            if not entry_data and i < len(entries_data):
                entry_data = entries_data[i]

            bullets = proj.descriptions or []
            bullet_count = len(bullets)
            
            # Map bullet suggestions
            suggestions = [
                BulletSuggestion(
                    bullet_index=s.get("bullet_index", 0),
                    original_bullet=s.get("original_bullet", ""),
                    context=s.get("context", ""),
                    advice=_clean_suggestion(s.get("advice", s.get("suggestion", ""))),
                    rewrites=[
                        {"label": r.get("label", "Alternative"), "content": r.get("content", "")}
                        for r in s.get("rewrites", [])
                    ]
                )
                for s in entry_data.get("suggestions", [])
            ]

            result.append(
                ProjectsAnalysis(
                    entry_index=i,
                    entry_name=proj.name or "Project",
                    bullet_count=bullet_count,
                    bullet_length_avg=int(sum(len(d) for d in bullets) / max(bullet_count, 1)) if bullets else 0,
                    star_principle_score=entry_data.get("star_score", 5.0),
                    star_principle_reasoning=entry_data.get("star_reasoning", "Analysis based on provided bullets."),
                    has_quantifiable_metrics=any("%" in b or any(c.isdigit() for c in b) for b in bullets),
                    metrics_count=sum(1 for b in bullets if "%" in b or any(c.isdigit() for c in b)),
                    impact_score=entry_data.get("score", 10.0) / 1.5,
                    issues=[],
                    suggestions=suggestions,
                    good_things=entry_data.get("good_things", []),
                    recommendation=entry_data.get("recommendation", "keep"),
                    score=entry_data.get("score", 10.0),
                )
            )

        return result

    except Exception as e:
        print(f"Projects analysis fallback triggered: {e}")
        return _fallback_projects_analysis(resume)


def _fallback_projects_analysis(resume):
    """Fallback analysis when LLM fails - simplified."""
    result = []
    for i, proj in enumerate(resume.projects):
        bullets = proj.descriptions or []
        bullet_count = len(bullets)
        metrics_found = sum(1 for b in bullets if "%" in b or any(c.isdigit() for c in b))

        result.append(
            ProjectsAnalysis(
                entry_index=i,
                entry_name=proj.name or "Project",
                bullet_count=bullet_count,
                bullet_length_avg=int(sum(len(d) for d in bullets) / max(bullet_count, 1)) if bullets else 0,
                star_principle_score=5.0,
                star_principle_reasoning="Fallback analysis triggered.",
                has_quantifiable_metrics=metrics_found > 0,
                metrics_count=metrics_found,
                impact_score=5.0,
                issues=[AnalysisIssue(issue="Analyzer fallback", severity="low", reason="LLM failed to respond")],
                suggestions=[BulletSuggestion(bullet_index=0, original_bullet=bullets[0] if bullets else "", context="Fallback", advice="Review STAR format", rewrites=[])],
                good_things=["Project listed"],
                recommendation="revise",
                score=10.0,
            )
        )
    return result
