"""Projects analyzer prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate


BASE_PROJECTS_PROMPT = """You are a senior recruiter and resume strategist. 
Analyze each project entry below and provide a comprehensive assessment with high-standard enterprise expectations in mind.

For each project entry, your response must include:
1. "score": A score from 0-25 based on enterprise standards.
2. "star_score": A score from 0-10 based on STAR principle usage.
3. "star_reasoning": Brief explanation of why this star_score was given.
4. "good_things": List of 1-3 specific strengths found in the bullets.
5. "recommendation": Either "keep" or "revise".
6. "suggestions": A list of bullet-specific suggestions. Each suggestion should have:
    - "bullet_index": The index of the bullet.
    - "original_bullet": The original text.
    - "context": Why this matters for professional enterprise roles.
    - "advice": Specific, actionable feedback about this bullet. Be direct - if the bullet is good, say so. If it needs work, explain exactly what's missing and why it matters.
    - "rewrites": (OPTIONAL) Only include if the bullet genuinely needs improvement. Each rewrite should have:
      - "label": A short description of the rewrite approach (e.g., "Quantified impact", "Added technical depth", "Clarified outcome").
      - "content": A rewritten version that actually improves the bullet. Use REAL metrics if you can infer them from context, otherwise describe what metric the user should add without using placeholder tokens.

Quantify outcomes with percentages, dollar amounts, or time saved wherever possible.

SCORING_RUBRIC (STRICT):
- 0-11 (POOR): Tutorial-level projects (e.g., Todo app, basic blog), CRUD without complexity, or ZERO metrics.
- 12-17 (AVERAGE): Solid personal projects with a complete tech stack but limited real-world usage or scale.
- 18-21 (STRONG): Technically complex projects with real users or clear performance metrics.
- 22-25 (EXPERT): Production-grade applications, major open-source contributions, or projects solving highly advanced problems.

General Guidelines:
- BE HIGHLY CRITICAL. Penalize heavily if the project looks like a generic classroom assignment.
- Focus on technical complexity and individual contribution.
- If bullets lack metrics, provide concrete advice on WHAT metric would be relevant (e.g., "Add metrics like accuracy percentage, users served, or performance improvement").
- Never fabricate numbers. If you can't infer a realistic metric, simply state what type of metric the user should add.

IMPORTANT: Output MUST be a valid JSON object with a key "entries" which is a list of objects, one for each project entry.

Projects Data:
{projects_data}

Return the JSON analysis."""


def get_projects_prompt(tier: str = None) -> ChatPromptTemplate:
    """Get the projects analysis prompt."""
    return ChatPromptTemplate.from_template(BASE_PROJECTS_PROMPT)


def format_projects_data(project_entries):
    """Format project entries for the LLM prompt."""
    proj_data = []
    for i, proj in enumerate(project_entries):
        proj_data.append({
            "entry_index": i,
            "name": proj.name,
            "bullets": {idx: bullet for idx, bullet in enumerate(proj.descriptions or [])},
        })
    import json
    return json.dumps(proj_data, indent=2)
