import json
from ..llm.client import llm
from .schemas import ExperienceAnalysis, AnalysisIssue


EXPERIENCE_ANALYZER_PROMPT = """You are a resume analysis expert with 10+ years of recruiting experience. You've screened thousands of resumes and know exactly what makes a candidate stand out.

STAR Method Background:
- S - Situation: The context or background of your experience
- T - Task: Your specific responsibility or challenge
- A - Action: What you did specifically (use strong action verbs)
- R - Result: The outcome - quantify with numbers, percentages, impact

Example of STAR format:
"S (Situation): Built an AI agent for 90,000+ users on the Aatmunn platform
T (Task): Enable natural language navigation across 55 screens
A (Action): Architected microservices with FastAPI, built RAG engine using pgvector
R (Result): Enabled automatic task execution, improved user engagement by X%"

Recruiter Perspective - What hiring managers look for in 6-10 seconds:
1. IMPACT: Can you show measurable results? Recruiters skip vague duties.
2. ACTION VERBS: Strong, specific verbs (built, led, architected, reduced, increased)
3. QUANTIFIABLE METRICS: Numbers, %, $, time saved, users affected
4. BREVITY: Bullet points should be 1-2 lines max, ~15-30 words each
5. RELEVANCE: Does this align with the job requirements?
6. SCANNABILITY: Use bullet points, not paragraphs

For each experience entry, evaluate:
1. Content Quality Score (0-10): Does it have clear S-T-A-R elements?
   - 9-10: Excellent - Clear STAR with quantified results
   - 7-8: Good - Has STAR elements, some results
   - 5-6: Average - Some STAR, not fully structured
   - 3-4: Needs Improvement - Vague, no clear results
   - 1-2: Poor - Duty-only, no results

2. Bullet Quality: 3-5 bullets optimal, each 1-2 lines (15-30 words)
3. Metrics: Look for numbers, %, $, improvements
4. Recruiter Scan Test: Would a recruiter understand your impact in <10 seconds?

For each experience entry, return JSON:
{
    "entry_index": 0,
    "entry_summary": "Company - Role",
    "bullet_count": number,
    "bullet_length_avg": average characters,
    "star_principle_score": number (0-10),
    "star_principle_reasoning": "explanation of STAR usage quality",
    "has_quantifiable_metrics": true/false,
    "metrics_count": number,
    "impact_score": number (0-10),
    "issues": [{"issue": "description", "severity": "high/medium/low", "reason": "explanation"}],
    "suggestions": ["specific suggestion referencing actual content: 'You wrote X but recruiter needs Y'", "another specific suggestion"],
    "good_things": ["what's already good about this entry: specific strong points a recruiter would appreciate"],
    "recommendation": "keep/revise/remove",
    "score": number (out of 25)
}

IMPORTANT - Both suggestions AND good_things are required and MUST be specific:
- Suggestions: What can be IMPROVED - be specific and contextual. NEVER use generic advice like "Add metrics". INSTEAD, say "In your 'Software Engineer' role, the bullet about 'improving API speed' is missing a specific metric like 'reduced latency by 40%'".
- Good Things: What's already GOOD - highlight strengths like clear action verbs, specific metrics, good structure, relevant achievements. Be specific: "Your use of 'Architected' in the AWS project clearly conveys technical leadership."

Scoring: Good content with results/metrics = HIGHER scores (15-22/25).
Only give low scores (<10) for vague, duty-only descriptions.
EVERY SUGGESTION MUST REFERENCE ACTUAL TEXT FROM THE RESUME TO PROVE WE ANALYZED IT.
NO GENERIC ADVICE: Never say "Add metrics" or "Use STAR". Instead, say "You mentioned 'Built an API', but recruiters want to see 'Built a Python API handling 5k requests/sec' to understand scale."
IF AN ENTRY IS GOOD: Don't force a suggestion; but ensure the 'good_things' explain WHY it's good from a recruiter's POV."""


def analyze_experience(resume) -> list[ExperienceAnalysis]:
    """Analyze all experience entries using LLM"""

    if not resume.experience:
        return []

    # Build experience data for LLM
    exp_data = []
    for i, exp in enumerate(resume.experience):
        exp_data.append(
            {
                "index": i,
                "company": exp.company,
                "title": exp.title,
                "start_date": exp.start_date,
                "end_date": exp.end_date,
                "descriptions": exp.descriptions,
            }
        )

    prompt = f"""{EXPERIENCE_ANALYZER_PROMPT}

Experience Data:
{json.dumps(exp_data, indent=2)}

Return a JSON array of analysis objects for each experience entry."""

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

        # Convert to ExperienceAnalysis objects
        result = []
        for analysis in analyses:
            # Handle missing fields with defaults
            result.append(
                ExperienceAnalysis(
                    entry_index=analysis.get("entry_index", 0),
                    entry_summary=analysis.get("entry_summary", ""),
                    bullet_count=analysis.get("bullet_count", 0),
                    bullet_length_avg=analysis.get("bullet_length_avg", 0),
                    star_principle_score=analysis.get("star_principle_score", 5.0),
                    star_principle_reasoning=analysis.get(
                        "star_principle_reasoning", ""
                    ),
                    has_quantifiable_metrics=analysis.get(
                        "has_quantifiable_metrics", False
                    ),
                    metrics_count=analysis.get("metrics_count", 0),
                    impact_score=analysis.get("impact_score", 5.0),
                    issues=[
                        AnalysisIssue(**issue) for issue in analysis.get("issues", [])
                    ],
                    suggestions=analysis.get("suggestions", []),
                    good_things=analysis.get("good_things", []),
                    recommendation=analysis.get("recommendation", "keep"),
                    score=analysis.get("score", 10.0),
                )
            )

        return result

    except Exception as e:
        print(f"Experience analysis fallback triggered: {e}")
        # Fallback: return basic analysis for each experience
        result = []
        for i, exp in enumerate(resume.experience):
            bullets = exp.descriptions or []
            bullet_count = len(bullets)
            
            # Heuristic suggestions
            fallback_suggestions = []
            if bullet_count < 3:
                fallback_suggestions.append(f"In your role at {exp.company}, you only have {bullet_count} bullets. Aim for 3-5 to fully showcase your impact.")
            
            if not any("%" in b or any(c.isdigit() for c in b) for b in bullets):
                fallback_suggestions.append(f"The description for {exp.title} lacks metrics. Try adding growth percentages or user counts (e.g., 'improved throughput by 20%').")
            
            if not fallback_suggestions:
                fallback_suggestions = ["Focus on specific achievements rather than just listing duties."]

            result.append(
                ExperienceAnalysis(
                    entry_index=i,
                    entry_summary=f"{exp.company} - {exp.title}",
                    bullet_count=bullet_count,
                    bullet_length_avg=int(sum(len(d) for d in bullets) / max(bullet_count, 1)),
                    star_principle_score=5.0,
                    star_principle_reasoning="Unable to perform deep LLM analysis - using heuristic fallback.",
                    has_quantifiable_metrics=False,
                    metrics_count=0,
                    impact_score=5.0,
                    issues=[AnalysisIssue(issue="Analyzer connection glitch", severity="low", reason="Falling back to simple heuristics")],
                    suggestions=fallback_suggestions,
                    good_things=[f"Professional entry for {exp.title} detected"],
                    recommendation="keep",
                    score=10.0,
                )
            )
        return result
