import json
from ..llm.client import llm
from .schemas import ExperienceAnalysis, AnalysisIssue, BulletSuggestion


STRONG_ACTION_VERBS = {
    "architected", "spearheaded", "orchestrated", "pioneered", "revolutionized",
    "transformed", "optimized", "streamlined", "automated", "accelerated",
    "delivered", "launched", "scaled", "reduced", "increased", "improved",
    "designed", "implemented", "developed", "built", "led", "owned",
    "pivoted", "mentored", "drove", "shipped", "enhanced", "modernized"
}

SCALE_PATTERNS = {
    "gpu", "gpus", "users", "requests", "queries", "million", "billion",
    "servers", "nodes", "clusters", "day", "month", "year", "concurrent"
}


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


METRIC_CONTEXT_PATTERNS = {
    "latency": ("reduction", "[~50–70%]"),  # latency → suggest ~50-70% reduction
    "response time": ("reduction", "[~50–70%]"),
    "throughput": ("improvement", "[X]%"),  # throughput → generic
    "accuracy": ("improvement", "[~3–5%]"),  # accuracy → small improvement range
    "error": ("reduction", "[~30–50%]"),
    "cost": ("reduction", "[~20–40%]"),
    "time": ("saved", "[X]%"),
    "speed": ("improvement", "[X]%"),
    "users": ("scale", "[Y]k"),
    "requests": ("scale", "[Z]k/day"),
    "queries": ("scale", "[Z]k/day"),
    "memory": ("reduction", "[~30–50%]"),
    "gpu": ("scale", "[Y] GPUs"),
}


def _extract_metric_context(bullet: str) -> tuple[str, str] | None:
    """Extract metric category from bullet to suggest appropriate placeholder."""
    bullet_lower = bullet.lower()
    for term, (context_type, placeholder) in METRIC_CONTEXT_PATTERNS.items():
        if term in bullet_lower:
            return (context_type, placeholder)
    return None


def _detect_bullet_strengths(bullets: list[str]) -> list[str]:
    """Generate specific, non-generic strengths based on actual bullet content."""
    strengths = set()
    
    for bullet in bullets:
        bullet_lower = bullet.lower()
        
        has_tech_stack = any(term in bullet_lower for term in [
            "python", "java", "react", "api", "docker", "kubernetes", 
            "aws", "gcp", "sql", "pytorch", "tensorflow", "vue",
            "node", "fastapi", "flask", "django", "spring", "go", "rust"
        ])
        if has_tech_stack:
            strengths.add("Clear tech stack mentioned")
        
        has_business_outcome = any(term in bullet_lower for term in [
            "revenue", "customer", "user", "engagement", "retention",
            "conversion", "sales", "business", "product", "stakeholder"
        ])
        if has_business_outcome:
            strengths.add("Directly tied to business outcome")
        
        has_scale = any(term in bullet_lower for term in SCALE_PATTERNS)
        if has_scale:
            strengths.add("Shows scale awareness")
        
        first_word = bullet.split()[0].lower() if bullet.split() else ""
        if first_word in STRONG_ACTION_VERBS:
            strengths.add("Strong action verb usage")
        
        has_metric = "%" in bullet or any(c.isdigit() for c in bullet)
        if has_metric:
            strengths.add("Includes quantified metrics")
    
    return list(strengths) if strengths else []


EXPERIENCE_ANALYZER_PROMPT = """You are a senior recruiter and resume strategist. For each bullet point below, provide exactly ONE actionable improvement suggestion.

Your response must include:
- "context": Why this matters (1 sentence). NO "Situation:" or "Task:" labels - just conversational framing. Max 15 words.
- "suggestion": Actionable tip - what to add or change. Max 20 words. Never prepend with "Add this to demonstrate impact".

Guidelines:
- If the bullet lacks metrics, suggest the TYPE of metric using placeholders based on the bullet's context:
  - If bullet mentions "latency", "response time" → use "[~50–70%] reduction"
  - If bullet mentions "users", "requests" → use "[Y]k scale"
  - If bullet mentions "accuracy" → use "[~3–5%] improvement"
  - Otherwise use generic [X]%, [Y]k, [Z]
- If the bullet already has a number, suggest how to make it more powerful.
- Mention missing TECHNICAL DEPTH (e.g., frameworks, tools, scale).
- Never invent absolute figures; use placeholders unless the bullet already contains them.

Example:
Input: "Reduced latency across 55+ screens with LLM-powered intent detection."
Output: {"context": "Recruiters want measurable impact", "suggestion": "Add [~50–70%] latency reduction and GPUs used to show scale"}

IMPORTANT:
- Output MUST be a JSON array of objects with: entry_index, bullet_index, original_bullet, context, suggestion
- If a bullet is already strong, you may skip it"""


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
                context=item.get("context"),
                suggestion=_clean_suggestion(item.get("suggestion", ""))
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
            
            # Detect STAR framing elements
            bullets_text = " ".join(bullets).lower()
            has_situation_task = any(word in bullets_text for word in [
                "when", "during", "while", "facing", "identifying", "assigned", "responsible"
            ])
            has_quantified_result = "%" in " ".join(bullets) or "k" in " ".join(bullets) or "m" in " ".join(bullets)
            
            # Score based on: bullet count (5pts) + metrics (10pts)
            bullet_score = min(5.0, bullet_count * 1.5)
            metric_score = min(10.0, metric_ratio * 10)
            calculated_score = bullet_score + metric_score
            
            # Stricter STAR principle score
            base_star = metric_ratio * 5
            framing_bonus = 2.0 if has_situation_task else 0
            result_bonus = 2.0 if metrics_found > 0 else 0
            action_bonus = 1.0 if any(b.split()[0].lower() in STRONG_ACTION_VERBS for b in bullets if b.split()) else 0
            star_score = min(10.0, base_star + framing_bonus + result_bonus + action_bonus)
            
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
                    good_things=_detect_bullet_strengths(bullets),
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
            
            # Stricter STAR scoring in fallback too
            bullets_text = " ".join(bullets).lower()
            has_situation_task = any(word in bullets_text for word in [
                "when", "during", "while", "facing", "identifying", "assigned", "responsible"
            ])
            base_star = metric_ratio * 5
            framing_bonus = 2.0 if has_situation_task else 0
            result_bonus = 2.0 if metrics_found > 0 else 0
            action_bonus = 1.0 if any(b.split()[0].lower() in STRONG_ACTION_VERBS for b in bullets if b.split()) else 0
            star_score = min(10.0, base_star + framing_bonus + result_bonus + action_bonus)
            recommendation = "keep" if calculated_score >= 12 else "revise"
            
            # Build suggestions
            fallback_suggestions = []
            for idx, bullet in enumerate(bullets):
                if bullet_count < 3:
                    ctx = f"You only have {bullet_count} bullets at {exp.company}"
                    sug_text = f"Aim for 3-5 bullets to fully showcase your impact"
                elif not any("%" in b or any(c.isdigit() for c in b) for b in bullets):
                    ctx = f"The description for {exp.title} lacks quantified metrics"
                    sug_text = f"Add growth percentages (e.g., 'improved throughput by [X]%')"
                else:
                    ctx = "Focus on specific achievements rather than just listing duties"
                    sug_text = "Consider adding more context around problem solved"
                fallback_suggestions.append(BulletSuggestion(
                    bullet_index=idx,
                    original_bullet=bullet,
                    context=ctx,
                    suggestion=sug_text
                ))
            if not fallback_suggestions:
                fallback_suggestions = [BulletSuggestion(
                    bullet_index=0,
                    original_bullet=bullets[0] if bullets else "",
                    context="Add metrics to strengthen your descriptions",
                    suggestion="Quantify your impact with percentages or numbers"
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
                    good_things=_detect_bullet_strengths(bullets),
                    recommendation=recommendation,
                    score=round(calculated_score, 2),
                )
            )
        return result


