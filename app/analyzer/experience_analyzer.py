import json
from ..llm.client import llm
from .schemas import ExperienceAnalysis, AnalysisIssue, BulletSuggestion


EXPERIENCE_ANALYZER_PROMPT = """You are a senior recruiter and resume strategist. For each bullet point below, provide exactly ONE actionable improvement suggestion.

Your suggestion must:
- Be phrased as coaching advice, not a command.
- Focus on the STAR framework: Situation, Task, Action, Result.
- Identify what's missing for a recruiter: quantifiable impact, scale, problem solved, or technical depth.
- If the bullet lacks metrics, suggest the exact TYPE of metric to add (e.g., "time saved", "accuracy gain vs. baseline", "throughput increase", "cost reduction") and use placeholders like [X]%, [Y]k, [Z] GPUs.
- If the bullet already has a number, show how to make it more powerful by adding context.
- Highlight the PROBLEM that was solved and why it mattered.
- Mention any missing TECHNICAL DEPTH (e.g., frameworks, tools, optimizations, scale).
- Never invent absolute figures; always use placeholders [X], [Y], [Z] unless the bullet already contains them.
- The suggestion should be crisp, at most 2 sentences, and end with a call to action like "Add this to demonstrate impact."

Example:
Input bullet: "Developed key components: patch embedding, positional encoding, multi-head self-attention, and transformer encoder blocks without relying on external ViT libraries."
Suggestion: "Show the impact of building from scratch: did this achieve [X]% higher throughput or [Y]% accuracy versus using a library? Mention if it solved a deployment constraint (e.g., lightweight runtime) and any technical depth like memory optimizations. Add a placeholder like 'achieved [X]% throughput increase on [Y] GPUs' to quantify the result."

IMPORTANT:
- Output MUST include the full original bullet text for each suggestion
- Use placeholders like [X]% or [Y] for missing metrics—do NOT fabricate numbers
- Sound like a professional resume coach: encouraging but direct
- Return a JSON array of suggestions for ALL bullets across ALL entries"""


def analyze_experience(resume) -> list[ExperienceAnalysis]:
    """Analyze all experience entries using LLM"""

    if not resume.experience:
        return []

    # Build experience data for LLM with numbered bullets
    exp_data = []
    for i, exp in enumerate(resume.experience):
        exp_data.append(
            {
                "entry_index": i,  # Include entry_index for each experience entry
                "company": exp.company,
                "title": exp.title,
                "start_date": exp.start_date,
                "end_date": exp.end_date,
                "bullets": {idx: bullet for idx, bullet in enumerate(exp.descriptions or [])},
            }
        )

    prompt = f"""{EXPERIENCE_ANALYZER_PROMPT}

Experience Data:
{json.dumps(exp_data, indent=2)}

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
        entry_suggestions = {}  # entry_index -> list of BulletSuggestion
        for item in bullet_suggestions:
            entry_idx = item.get("entry_index", 0)
            if entry_idx not in entry_suggestions:
                entry_suggestions[entry_idx] = []
            entry_suggestions[entry_idx].append(BulletSuggestion(
                bullet_index=item.get("bullet_index", 0),
                original_bullet=item.get("original_bullet", ""),
                suggestion=item.get("suggestion", "")
            ))

# Build ExperienceAnalysis objects with actual scoring
        result = []
        for i, exp in enumerate(resume.experience):
            suggestions = entry_suggestions.get(i, [])
            
            # Calculate actual impact based on metrics presence
            bullets = exp.descriptions or []
            bullet_count = len(bullets)
            metrics_found = sum(1 for b in bullets if "%" in b or any(c.isdigit() for c in b))
            metric_ratio = metrics_found / max(bullet_count, 1)
            
            # Score based on: bullet count (5pts) + metrics (10pts)
            bullet_score = min(5.0, bullet_count * 1.5)
            metric_score = min(10.0, metric_ratio * 10)
            calculated_score = bullet_score + metric_score
            
            # Star principle score derived from metric presence
            star_score = min(10.0, (metric_ratio * 8) + 3)
            
            # Determine recommendation based on score
            recommendation = "keep" if calculated_score >= 12 else "revise"
            
            result.append(
                ExperienceAnalysis(
                    entry_index=i,
                    entry_summary=f"{exp.company} - {exp.title}" if exp.company else "Experience",
                    bullet_count=bullet_count,
                    bullet_length_avg=int(sum(len(d) for d in bullets) / max(bullet_count, 1)),
                    star_principle_score=round(star_score, 2),
                    star_principle_reasoning=f"Found {metrics_found} metrics in {bullet_count} bullets" if metrics_found else "Add quantifiable metrics to improve score",
                    has_quantifiable_metrics=metrics_found > 0,
                    metrics_count=metrics_found,
                    impact_score=round(calculated_score / 1.5, 2),
                    issues=[],
                    suggestions=suggestions,
                    good_things=["Strong entry with metrics" if metrics_found else "Entry found" for _ in suggestions] if suggestions else ["Strong entry" if bullets else "No descriptions found"],
                    recommendation=recommendation,
                    score=round(calculated_score, 2),
                )
            )

        return result

    except Exception as e:
        print(f"Experience analysis fallback triggered: {e}")
        result = []
        for i, exp in enumerate(resume.experience):
            bullets = exp.descriptions or []
            bullet_count = len(bullets)
            
            # Calculate actual metrics in fallback too
            metrics_found = sum(1 for b in bullets if "%" in b or any(c.isdigit() for c in b))
            metric_ratio = metrics_found / max(bullet_count, 1)
            
            # Lower scores in fallback - we're being strict now
            bullet_score = min(5.0, bullet_count * 1.5)
            metric_score = min(10.0, metric_ratio * 10)
            calculated_score = bullet_score + metric_score
            
            star_score = min(10.0, (metric_ratio * 8) + 3)
            recommendation = "keep" if calculated_score >= 12 else "revise"
            
            # Build suggestions
            fallback_suggestions = []
            for idx, bullet in enumerate(bullets):
                if bullet_count < 3:
                    sug_text = f"In your role at {exp.company}, you only have {bullet_count} bullets. Aim for 3-5 to fully showcase your impact."
                elif not any("%" in b or any(c.isdigit() for c in b) for b in bullets):
                    sug_text = f"The description for {exp.title} lacks metrics. Try adding growth percentages (e.g., 'improved throughput by [X]%')."
                else:
                    sug_text = "Focus on specific achievements rather than just listing duties."
                fallback_suggestions.append(BulletSuggestion(
                    bullet_index=idx,
                    original_bullet=bullet,
                    suggestion=sug_text
                ))
            if not fallback_suggestions:
                fallback_suggestions = [BulletSuggestion(
                    bullet_index=0,
                    original_bullet=bullets[0] if bullets else "",
                    suggestion="Consider adding more specific metrics to your descriptions."
                )]
            result.append(
                ExperienceAnalysis(
                    entry_index=i,
                    entry_summary=f"{exp.company} - {exp.title}",
                    bullet_count=bullet_count,
                    bullet_length_avg=int(sum(len(d) for d in bullets) / max(bullet_count, 1)),
                    star_principle_score=round(star_score, 2),
                    star_principle_reasoning=f"No LLM analysis - found {metrics_found} metrics in fallback" if metrics_found else "Add metrics to improve score",
                    has_quantifiable_metrics=metrics_found > 0,
                    metrics_count=metrics_found,
                    impact_score=round(calculated_score / 1.5, 2),
                    issues=[AnalysisIssue(issue="Analyzer glitch", severity="low", reason="Falling back to simple heuristics")],
                    suggestions=fallback_suggestions,
                    good_things=[f"Professional entry for {exp.title} detected"],
                    recommendation=recommendation,
                    score=round(calculated_score, 2),
                )
            )
        return result


