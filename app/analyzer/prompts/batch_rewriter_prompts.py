"""Batch rewriter prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate


BASE_REWRITER_PROMPT = """You are an expert resume writer. Your task is to rephrase resume bullets to sound natural and impactful — like a real person wrote them, not an AI.

Original Bullet: {original_bullet}
Context: {context}
Recruiter Advice: {advice}
Repeated words to avoid in this section: {repeated_words}
Words to avoid for variety (used in other rewrites): {accumulated_used_words}

Output:
- If the bullet is already strong and well-written, return empty: {{"content": ""}}
- IMPORTANT: Do NOT return a rewrite that is nearly identical to the original. If you would only change 1-2 words, return empty instead — a near-duplicate rewrite adds no value.
- If it can be improved, provide exactly 1 rephrased version that is CLEARLY different from the original
- NEVER inject metrics, numbers, percentages, or placeholder values that are not in the original bullet
- Only rephrase how the same message is conveyed — preserve the original meaning and facts exactly
- Avoid the listed repeated words — choose different synonyms instead

TONE RULES (critical — these distinguish good rewrites from bad ones):
- Write like a recruiter would describe the work, not like a corporate thesaurus.
- Keep the original's voice. If the original is direct and conversational, stay that way.
- Do NOT pad simple statements with fancy vocabulary. "Built an API" is fine — it does not need to become "Orchestrated a sophisticated API architecture."
- Prefer short, punchy sentences over long, winding ones.
- The goal is clarity and impact, not sounding impressive.

BAD vs GOOD examples:
- BAD: "Orchestrated an interactive guide that interprets intent and executes actions across 55+ screens"
  GOOD: "Built an AI assistant that automated user workflows across 55+ application screens"
- BAD: "Spearheaded the development of a high-throughput backend capable of handling 10,000+ daily conversational exchanges"
  GOOD: "Built backend infrastructure to handle 10,000+ daily AI interactions for 90,000+ active users"
- BAD: "Architected a scalable data pipeline leveraging event-driven patterns"
  GOOD: "Built a data pipeline using event-driven architecture to process requests in real time"

NEVER use these corporate filler words: orchestrated, spearheaded, architected, leveraged, synergized,facilitated, conceptualized, harnessed, endeavored, commence, utilize, effectuate.

Evaluation criteria (check each bullet against these):
1. Natural language — does it sound like a real person describing real work?
2. Cause-effect clarity — does the bullet show what was done AND what resulted?
3. Specific context — prefer concrete details over vague/generic filler

IMPORTANT: Respond with ONLY the JSON object. No explanation, no markdown, no code fences.
Example: {{"content": "Your rephrased bullet here."}}"""

BATCH_REWRITER_PROMPT = """You are an expert resume writer. Your task is to rephrase a batch of resume bullets to sound natural and impactful — like a real person wrote them, not an AI.

Context: {context}

Bullets to rephrase:
{bullets_data}

Overused words in the original resume (ABSOLUTELY AVOID these): {repeated_words}
Words used in other rephrased bullets (ABSOLUTELY AVOID these): {accumulated_used_words}

TONE RULES (critical — these distinguish good rewrites from bad ones):
- Write like a recruiter would describe the work, not like a corporate thesaurus.
- Keep the original's voice. If the original is direct and conversational, stay that way.
- Do NOT pad simple statements with fancy vocabulary. "Built an API" is fine — it does not need to become "Orchestrated a sophisticated API architecture."
- Prefer short, punchy sentences over long, winding ones.
- The goal is clarity and impact, not sounding impressive.

BAD vs GOOD examples:
- BAD: "Orchestrated an interactive guide that interprets intent and executes actions across 55+ screens"
  GOOD: "Built an AI assistant that automated user workflows across 55+ application screens"
- BAD: "Spearheaded the development of a high-throughput backend capable of handling 10,000+ daily conversational exchanges"
  GOOD: "Built backend infrastructure to handle 10,000+ daily AI interactions for 90,000+ active users"
- BAD: "Architected a scalable data pipeline leveraging event-driven patterns"
  GOOD: "Built a data pipeline using event-driven architecture to process requests in real time"

NEVER use these corporate filler words: orchestrated, spearheaded, architected, leveraged, synergized, facilitated, conceptualized, harnessed, endeavored, commence, utilize, effectuate.

CRITICAL DIVERSITY RULES:
- Every rephrased bullet in this batch must use DIFFERENT action verbs. No two bullets should start with the same verb.
- Do NOT use any word from the "Overused" or "Words used in other rewrites" lists — anywhere in the bullet.
- Scan your own output before responding: if any word appears in more than one bullet, replace it with a synonym.
- Vary sentence structure: don't start every bullet the same way.

Other constraints:
- Provide exactly one rephrased version for each bullet ID provided.
- If a bullet is already excellent, return empty string for that ID: {{"b0": ""}} — do NOT return a near-duplicate.
- IMPORTANT: A rewrite that changes only 1-2 words is worse than no rewrite. If you can't make a meaningful improvement, return empty.
- NEVER invent new facts, metrics, numbers, percentages, or technologies not present in the original.

Response Format:
Respond with ONLY a JSON object mapping bullet IDs to their new content.
Example:
{{
  "id_1": "Built a data pipeline using event-driven architecture...",
  "id_2": "Led a cross-functional team of 10 to deliver..."
}}"""


def get_batch_rewriter_prompt(is_batch: bool = False) -> ChatPromptTemplate:
    """Get the batch rewriter prompt template."""
    return ChatPromptTemplate.from_template(BATCH_REWRITER_PROMPT if is_batch else BASE_REWRITER_PROMPT)


def format_batch_rewriter_data(original_bullet, advice, context, repeated_words=None, accumulated_used_words=None):
    """Format single rewriter data for the LLM prompt."""
    return {
        "original_bullet": original_bullet,
        "context": context or "N/A",
        "advice": advice or "N/A",
        "repeated_words": ", ".join(repeated_words) if repeated_words else "None",
        "accumulated_used_words": ", ".join(accumulated_used_words) if accumulated_used_words else "None",
    }

def format_multi_bullet_data(bullets, context, repeated_words=None, accumulated_used_words=None):
    """Format multiple bullets for the batch rewriter prompt."""
    bullets_text = ""
    for b in bullets:
        bullets_text += f"- ID: {b['id']}\n  Original: {b['bullet']}\n  Advice: {b.get('advice', 'N/A')}\n\n"
    
    return {
        "context": context or "N/A",
        "bullets_data": bullets_text.strip(),
        "repeated_words": ", ".join(repeated_words) if repeated_words else "None",
        "accumulated_used_words": ", ".join(accumulated_used_words) if accumulated_used_words else "None",
    }
