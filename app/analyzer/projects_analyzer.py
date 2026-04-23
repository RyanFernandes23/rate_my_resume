import json
from ..llm.client import llm
from .schemas import ProjectsAnalysis, AnalysisIssue


PROJECTS_ANALYZER_PROMPT = """You are a resume analysis expert with 10+ years of recruiting experience. You've screened thousands of resumes and know exactly what makes a candidate stand out.

STAR Method Background:
- S - Situation: What problem/need the project addresses
- T - Task: Your specific role in the project
- A - Action: What you built/implemented (technologies, approach)
- R - Result: Outcome, impact, metrics

Example of STAR in projects:
"S (Situation): Users needed real-time answers from web data
T (Task): Build a chatbot that searches live web data
A (Action): Used Groq LLM, FastAPI, Chroma DB for semantic search
R (Result): Created full-stack system with 95% accuracy"

Recruiter Perspective - What hiring managers look for in 6-10 seconds:
1. TECHNICAL DEPTH: What technologies did you use? Show you know your stack
2. PROBLEM-SOLVING: What challenge did you solve? Why does it matter?
3. IMPACT: What was the outcome? Metrics, accuracy, users, performance gains
4. BREVITY: Project descriptions should be concise, 2-4 bullet points
5. SCANNABILITY: Can a recruiter quickly understand what you built?

Analyze each project entry:

1. Content Quality Score (0-10): STAR elements + technical depth
   - 9-10: Excellent - Clear STAR with tech stack and outcomes
   - 7-8: Good - Has STAR elements, some tech details
   - 5-6: Average - Basic description
   - 3-4: Needs Improvement - Vague
   - 1-2: Poor - Very minimal

2. Bullet Quality: 2-4 bullets per project
3. Technical Depth: Technologies, frameworks, tools used
4. Recruiter Scan Test: Would a recruiter understand your project in <10 seconds?

For each project, return JSON:
{
    "entry_index": 0,
    "entry_name": "Project Name",
    "bullet_count": number,
    "bullet_length_avg": number,
    "star_principle_score": number (0-10),
    "star_principle_reasoning": "explanation",
    "has_quantifiable_metrics": true/false,
    "metrics_count": number,
    "impact_score": number (0-10),
    "issues": [{"issue": "description", "severity": "high/medium/low", "reason": "explanation"}],
    "suggestions": ["specific suggestion referencing actual content: 'Your description mentions X but recruiter wants to see Y'", "another specific suggestion"],
    "good_things": ["what's already good about this project: specific strong points a recruiter would appreciate"],
    "recommendation": "keep/revise/remove",
    "score": number (out of 15)
}

IMPORTANT - Both suggestions AND good_things are required and MUST be specific:
- Suggestions: What can be IMPROVED - be specific and contextual. NEVER use generic advice. INSTEAD, say "In your 'E-commerce App' project, the description of the 'payment gateway' lacks detail on the tech stack—mention if you used Stripe or PayPal".
- Good Things: What's already GOOD - highlight strengths like clear tech stack, good problem-solution structure, impressive outcomes, technical depth. Be specific: "Your use of '95% accuracy' in the chatbot project is a strong, quantifiable result."

Scoring: Well-documented projects with tech stack get HIGHER scores (10-14/15).
EVERY SUGGESTION MUST REFERENCE ACTUAL TEXT FROM THE RESUME TO PROVE WE ANALYZED IT.
GENERIC SUGGESTIONS WILL BE PENALIZED."""


def analyze_projects(resume) -> list[ProjectsAnalysis]:
    """Analyze all project entries using LLM"""

    if not resume.projects:
        return []

    # Build project data for LLM
    proj_data = []
    for i, proj in enumerate(resume.projects):
        proj_data.append(
            {
                "index": i,
                "name": proj.name,
                "descriptions": proj.descriptions,
                "link": proj.link,
            }
        )

    prompt = f"""{PROJECTS_ANALYZER_PROMPT}

Projects Data:
{json.dumps(proj_data, indent=2)}

Return a JSON array of analysis objects for each project entry."""

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

        # Convert to ProjectsAnalysis objects
        result = []
        for analysis in analyses:
            result.append(
                ProjectsAnalysis(
                    entry_index=analysis.get("entry_index", 0),
                    entry_name=analysis.get("entry_name", ""),
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
                    score=analysis.get("score", 7.5),
                )
            )

        return result

    except Exception as e:
        # Fallback
        result = []
        for i, proj in enumerate(resume.projects):
            result.append(
                ProjectsAnalysis(
                    entry_index=i,
                    entry_name=proj.name,
                    bullet_count=len(proj.descriptions) if proj.descriptions else 0,
                    bullet_length_avg=int(
                        sum(len(d) for d in (proj.descriptions or []))
                        / max(len(proj.descriptions or []), 1)
                    ),
                    star_principle_score=5.0,
                    star_principle_reasoning="Unable to analyze - LLM error",
                    has_quantifiable_metrics=False,
                    metrics_count=0,
                    impact_score=5.0,
                    issues=[
                        AnalysisIssue(
                            issue="Could not analyze project",
                            severity="low",
                            reason=str(e),
                        )
                    ],
                    suggestions=["Review project descriptions for STAR format"],
                    good_things=["Has project entry with name clearly listed"],
                    recommendation="keep",
                    score=7.5,
                )
            )
        return result
