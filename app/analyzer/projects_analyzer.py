import json
from ..llm.client import llm
from .schemas import ProjectsAnalysis, AnalysisIssue, BulletSuggestion


PROJECTS_ANALYZER_PROMPT = """You are a senior recruiter and resume strategist. For each bullet point below, provide exactly ONE actionable improvement suggestion.

Your suggestion must:
- Be phrased as coaching advice, not a command.
- Focus on the STAR framework: Situation, Task, Action, Result.
- Identify what's missing for a recruiter: quantifiable impact, scale, problem solved, or technical depth.
- If the bullet lacks metrics, suggest the exact TYPE of metric to add (e.g., "accuracy", "latency reduction", "throughput increase", "users served") and use placeholders like [X]%, [Y]k, [Z] users.
- If the bullet already has a number, show how to make it more powerful by adding context.
- Highlight the PROBLEM that was solved and why it mattered.
- Mention any missing TECHNICAL DEPTH (e.g., frameworks, libraries, APIs, tools, optimizations).
- Never invent absolute figures; always use placeholders [X], [Y], [Z] unless the bullet already contains them.
- The suggestion should be crisp, at most 2 sentences, and end with a call to action like "Add this to demonstrate impact."

Example:
Input bullet: "Developed a RAG Chatbot using Groq's LLM and FastAPI backend with ChromaDB for vector storage."
Suggestion: "Add the impact: what accuracy or response time did this achieve? Mention the scale (e.g., [X] queries/day) and any technical wins like latency reduction or cost savings. Recruiters love seeing measurable results. Add a placeholder like 'achieving [Y]% accuracy and [Z]ms latency' to quantify the impact."

IMPORTANT:
- Output MUST include the full original bullet text for each suggestion
- Use placeholders like [X]% or [Y] for missing metrics—do NOT fabricate numbers
- Sound like a professional resume coach: encouraging but direct
- Return a JSON array of suggestions for ALL bullets across ALL projects"""


def analyze_projects(resume) -> list[ProjectsAnalysis]:
    """Analyze all project entries using LLM"""

    if not resume.projects:
        return []

    # Build project data for LLM with numbered bullets
    proj_data = []
    for i, proj in enumerate(resume.projects):
        proj_data.append(
            {
                "entry_index": i,  # Include entry_index for each project entry
                "name": proj.name,
                "bullets": {idx: bullet for idx, bullet in enumerate(proj.descriptions or [])},
                "link": proj.link,
            }
        )

    prompt = f"""{PROJECTS_ANALYZER_PROMPT}

Projects Data:
{json.dumps(proj_data, indent=2)}

Return a JSON array. For each bullet that needs improvement, output one object with entry_index, bullet_index, original_bullet, and suggestion.
If a bullet is already strong, you may skip it."""

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

        bullet_suggestions = json.loads(json_str)

        # Convert to BulletSuggestion objects and group by entry_index
        entry_suggestions = {}
        for item in bullet_suggestions:
            entry_idx = item.get("entry_index", 0)
            if entry_idx not in entry_suggestions:
                entry_suggestions[entry_idx] = []
            entry_suggestions[entry_idx].append(BulletSuggestion(
                bullet_index=item.get("bullet_index", 0),
                original_bullet=item.get("original_bullet", ""),
                suggestion=item.get("suggestion", "")
            ))

        # Build ProjectsAnalysis objects with actual scoring
        result = []
        for i, proj in enumerate(resume.projects):
            suggestions = entry_suggestions.get(i, [])
            
            # Calculate actual impact based on metrics presence
            bullets = proj.descriptions or []
            bullet_count = len(bullets)
            metrics_found = sum(1 for b in bullets if "%" in b or any(c.isdigit() for c in b))
            metric_ratio = metrics_found / max(bullet_count, 1)
            
            # Score based on: bullet count (4pts) + metrics (6pts) - total /15 
            bullet_score = min(4.0, bullet_count * 1.0)
            metric_score = min(6.0, metric_ratio * 6)
            calculated_score = bullet_score + metric_score
            
            # Star principle score derived from metric presence
            star_score = min(10.0, (metric_ratio * 8) + 2)
            
            # Determine recommendation based on score
            recommendation = "keep" if calculated_score >= 7 else "revise"
            
            result.append(
                ProjectsAnalysis(
                    entry_index=i,
                    entry_name=proj.name or "Project",
                    bullet_count=bullet_count,
                    bullet_length_avg=int(sum(len(d) for d in bullets) / max(bullet_count, 1)),
                    star_principle_score=round(star_score, 2),
                    star_principle_reasoning=f"Found {metrics_found} metrics in {bullet_count} bullets" if metrics_found else "Add quantifiable metrics to improve score",
                    has_quantifiable_metrics=metrics_found > 0,
                    metrics_count=metrics_found,
                    impact_score=round(calculated_score / 1.5, 2),
                    issues=[],
                    suggestions=suggestions,
                    good_things=["Strong project with metrics" if metrics_found else "Project entry found" for _ in suggestions] if suggestions else ["Well-documented project" if bullets else "Consider adding project details"],
                    recommendation=recommendation,
                    score=round(calculated_score, 2),
                )
            )

        return result

    except Exception as e:
        # Fallback - but now with stricter scoring
        result = []
        for i, proj in enumerate(resume.projects):
            suggestions = []
            bullets = proj.descriptions or []
            bullet_count = len(bullets)
            
            # Calculate metrics in fallback too
            metrics_found = sum(1 for b in bullets if "%" in b or any(c.isdigit() for c in b))
            metric_ratio = metrics_found / max(bullet_count, 1)
            
            # Lower scores in fallback
            bullet_score = min(4.0, bullet_count * 1.0)
            metric_score = min(6.0, metric_ratio * 6)
            calculated_score = bullet_score + metric_score
            
            star_score = min(10.0, (metric_ratio * 8) + 2)
            recommendation = "keep" if calculated_score >= 7 else "revise"
            
            for idx, bullet in enumerate(bullets):
                suggestions.append(BulletSuggestion(
                    bullet_index=idx,
                    original_bullet=bullet,
                    suggestion="Consider adding more specific metrics or tech stack details to strengthen this project description."
                ))
            result.append(
                ProjectsAnalysis(
                    entry_index=i,
                    entry_name=proj.name or "Project",
                    bullet_count=bullet_count,
                    bullet_length_avg=int(sum(len(d) for d in bullets) / max(bullet_count, 1)),
                    star_principle_score=round(star_score, 2),
                    star_principle_reasoning=f"No LLM - found {metrics_found} metrics in fallback" if metrics_found else "Add metrics to improve score",
                    has_quantifiable_metrics=metrics_found > 0,
                    metrics_count=metrics_found,
                    impact_score=round(calculated_score / 1.5, 2),
                    issues=[AnalysisIssue(issue="Could not analyze project", severity="low", reason=str(e))],
                    suggestions=suggestions,
                    good_things=["Has project entry with name clearly listed"],
                    recommendation=recommendation,
                    score=round(calculated_score, 2),
                )
            )
        return result
