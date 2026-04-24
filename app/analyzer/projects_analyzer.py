import json
from ..llm.client import llm
from .schemas import ProjectsAnalysis, AnalysisIssue, BulletSuggestion


STRONG_ACTION_VERBS = {
    "architected", "spearheaded", "orchestrated", "pioneered", "revolutionized",
    "transformed", "optimized", "streamlined", "automated", "accelerated",
    "delivered", "launched", "scaled", "reduced", "increased", "improved",
    "designed", "implemented", "developed", "built", "created", "engineered",
    "deployed", "integrated", "enhanced", "shipped", "built", "crafted"
}

ACADEMIC_LEARNING_KEYWORDS = {
    "from scratch", "implement", "learn", "understanding", "course",
    "cifar", "mnist", "tutorial", "practice", "study"
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
    "latency": ("reduction", "[~50–70%]"),
    "response time": ("reduction", "[~50–70%]"),
    "throughput": ("improvement", "[X]%"),
    "accuracy": ("improvement", "[~3–5%]"),
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


def _detect_project_strengths(bullets: list[str], project_name: str = "") -> list[str]:
    """Generate specific, non-generic strengths based on actual content."""
    strengths = set()
    name_lower = project_name.lower()
    all_text = " ".join(bullets).lower()
    
    is_academic_project = any(kw in all_text or kw in name_lower for kw in ACADEMIC_LEARNING_KEYWORDS)
    
    if is_academic_project:
        strengths.add("Learning-focused project (educational value)")
    else:
        has_tech_stack = any(term in all_text for term in [
            "python", "java", "react", "api", "docker", "kubernetes", 
            "aws", "gcp", "sql", "pytorch", "tensorflow", "vue",
            "node", "fastapi", "flask", "django", "go", "rust", "sql", "mongodb"
        ])
        if has_tech_stack:
            strengths.add("Clear tech stack mentioned")
    
    has_outcome = any(term in all_text for term in [
        "accuracy", "latency", "throughput", "users", "performance",
        "reduction", "improvement", "achieved", "result", "output"
    ])
    if has_outcome:
        strengths.add("Mentions measurable outcomes")
    
    has_scale = any(term in all_text for term in [
        "gpu", "gpus", "million", "billion", "concurrent", "scalable"
    ])
    if has_scale:
        strengths.add("Shows scale consideration")
    
    first_word = bullets[0].split()[0].lower() if bullets and bullets[0].split() else ""
    if first_word in STRONG_ACTION_VERBS:
        strengths.add("Strong action verb usage")
    
    has_metric = "%" in all_text or any(c.isdigit() for c in all_text)
    if has_metric:
        strengths.add("Includes quantified metrics")
    
    if "github" in all_text or "link" in all_text or "repository" in all_text:
        strengths.add("Has project link available")
    
    return list(strengths) if strengths else []


PROJECTS_ANALYZER_PROMPT = """You are a senior recruiter and resume strategist. For each bullet point below, provide exactly ONE actionable improvement suggestion.

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
- Mention missing TECHNICAL DEPTH (e.g., frameworks, libraries, APIs, tools).
- Never invent absolute figures; use placeholders unless the bullet already contains them.

Example:
Input: "Developed a RAG Chatbot using Groq's LLM and FastAPI backend with ChromaDB."
Output: {"context": "Recruiters want to see measurable outcomes on projects", "suggestion": "Add accuracy % and [Z]k queries/day to show scale"}

IMPORTANT:
- Output MUST be a JSON array of objects with: entry_index, bullet_index, original_bullet, context, suggestion
- If a bullet is already strong, you may skip it"""


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
                context=item.get("context"),
                suggestion=_clean_suggestion(item.get("suggestion", ""))
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
            
            # Detect project type for alternative scoring
            all_text = " ".join(bullets).lower() + " " + proj.name.lower()
            is_academic = any(kw in all_text for kw in ACADEMIC_LEARNING_KEYWORDS)
            
            # Score based on: bullet count (4pts) + metrics (6pts)
            bullet_score = min(4.0, bullet_count * 1.0)
            metric_score = min(6.0, metric_ratio * 6)
            calculated_score = bullet_score + metric_score
            
            # Stricter STAR principle score with academic consideration
            base_star = metric_ratio * 5
            framing_bonus = 1.5 if is_academic else 2.0 if any(
                kw in all_text for kw in ["achieved", "result", "outcome", "improved", "reduced"]
            ) else 0
            result_bonus = 2.0 if metrics_found > 0 else 0
            action_bonus = 1.0 if any(b.split()[0].lower() in STRONG_ACTION_VERBS for b in bullets if b.split()) else 0
            star_score = min(10.0, base_star + framing_bonus + result_bonus + action_bonus)
            
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
                    good_things=_detect_project_strengths(bullets, proj.name or ""),
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
            
            # Stricter STAR scoring in fallback too
            all_text = " ".join(bullets).lower() + " " + proj.name.lower()
            is_academic = any(kw in all_text for kw in ACADEMIC_LEARNING_KEYWORDS)
            base_star = metric_ratio * 5
            framing_bonus = 1.5 if is_academic else 2.0 if any(
                kw in all_text for kw in ["achieved", "result", "outcome", "improved", "reduced"]
            ) else 0
            result_bonus = 2.0 if metrics_found > 0 else 0
            action_bonus = 1.0 if any(b.split()[0].lower() in STRONG_ACTION_VERBS for b in bullets if b.split()) else 0
            star_score = min(10.0, base_star + framing_bonus + result_bonus + action_bonus)
            recommendation = "keep" if calculated_score >= 7 else "revise"
            
            for idx, bullet in enumerate(bullets):
                metrics_found_proj = "%" in bullet or any(c.isdigit() for c in bullet)
                ctx = "Recruiters want measurable outcomes on projects" if not metrics_found_proj else "Consider adding more context"
                suggestions.append(BulletSuggestion(
                    bullet_index=idx,
                    original_bullet=bullet,
                    context=ctx,
                    suggestion="Add accuracy %, latency ms, or users served" if not metrics_found_proj else "Add tech stack details if missing"
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
                    good_things=_detect_project_strengths(bullets, proj.name or ""),
                    recommendation=recommendation,
                    score=round(calculated_score, 2),
                )
            )
        return result
