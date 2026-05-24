"""Experience analyzer prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate


BASE_EXPERIENCE_PROMPT = """You are a senior recruiter and resume strategist. 
Analyze each experience entry below and provide a comprehensive assessment with high-standard enterprise expectations in mind.

For each experience entry, your response must include:
1. "score": A score from 0-25 based on enterprise standards.(this score should be evaluate based on below bullets)
2. "star_score": A score from 0-10 based on STAR principle usage.
3. "star_reasoning": Brief explanation of why this star_score was given.
4. "good_things": List of 1-3 specific strengths found in the bullets.
5. "recommendation": Either "keep" or "revise".
6. "suggestions": A list of bullet-specific suggestions. Each suggestion should have:
    - "bullet_index": The index of the bullet.
    - "original_bullet": The original text.
    - "context": Why this matters for professional enterprise roles.
    - "advice": Specific, actionable feedback about this bullet. IMPORTANT: AVOID generic praise like "This bullet is strong". If it is good, explain the specific technical or business impact demonstrated. If it needs work, focus exclusively on the missing metric or structural issue. DO NOT use repetitive phrases across different bullet points.,
    - "rewrites": (OPTIONAL) Only include if the bullet genuinely needs improvement. Each rewrite should have:
      - "label": A short description of the rewrite approach (e.g., "Quantified impact", "Added technical depth", "Clarified outcome").
      - "content": A rewritten version that actually improves the bullet. Use REAL metrics if you can infer them from context, otherwise describe what metric the user should add without using placeholder tokens.

Quantify impact using percentages, dollar amounts, or time saved wherever possible.

SCORING_RUBRIC (STRICT):
- 0-9 (POOR): Vague bullets, "responsible for" phrasing, ZERO metrics, or irrelevant tech stack.
- 10-15 (AVERAGE): Clear tasks but missing the 'Result' in STAR. Basic metrics used but impact feels small or common.
- 16-20 (STRONG): Strong STAR usage, clear quantifiable impact, and deep technical mastery.
- 21-25 (EXPERT): Exceptional impact (e.g., $1M+ saved, 90%+ optimization, led teams of 10+). Rare, unique technical or leadership achievement.

General Guidelines:
- BE CRITICAL. A 25/25 should be near-impossible to achieve. Most professional resumes should fall in the 10-18 range.
- PENALIZE HEAVILY (-5 to -10 points) if bullets lack quantifiable metrics (%, $, numbers).
- If bullets lack metrics, provide concrete advice on WHAT metric would be relevant.
- Require specific Technical Depth for Senior roles.
- Never fabricate numbers. If you can't infer a realistic metric, simply state what type of metric the user should add.

IMPORTANT: Output MUST be a valid JSON object with a key "entries" which is a list of objects, one for each experience entry.

Experience Data:
{experience_data}

Return the JSON analysis."""


def get_experience_prompt(tier: str = None) -> ChatPromptTemplate:
    """Get the experience analysis prompt."""
    return ChatPromptTemplate.from_template(BASE_EXPERIENCE_PROMPT)



def format_experience_data(experience_entries):
    """Format experience entries for the LLM prompt."""
    exp_data = []
    for i, exp in enumerate(experience_entries):
        exp_data.append({
            "entry_index": i,
            "company": exp.company,
            "title": exp.title,
            "bullets": {idx: bullet for idx, bullet in enumerate(exp.descriptions or [])},
        })
    import json
    return json.dumps(exp_data, indent=2)
