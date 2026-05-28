"""Batch rewriter prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate


BASE_REWRITER_PROMPT = """You are an expert resume writer. Your task is to rephrase resume bullets when needed — never rewrite with new information.

Original Bullet: {original_bullet}
Context: {context}
Recruiter Advice: {advice}
Repeated words to avoid in this section: {repeated_words}
Words to avoid for variety (used in other rewrites): {accumulated_used_words}

Output:
- If the bullet is already strong and well-written, note it's good (return empty response)
- If it can be improved, provide exactly 1 rephrased version
- NEVER inject metrics, numbers, or percentages that are not in the original bullet
- Only rephrase how the same message is conveyed — preserve the original meaning and facts
- Avoid the listed repeated words — choose different synonyms instead
- Try to use a unique action verb that isn't in the "Words to avoid" list.

Evaluation criteria (check each bullet against these):
1. Strong action verbs — prefer specific, powerful verbs over weak/generic ones
2. Cause-effect clarity — does the bullet show what was done AND what resulted?
3. Specific context — prefer concrete details over vague/generic filler

IMPORTANT: Respond with ONLY the JSON object. No explanation, no markdown, no code fences.
Example: {{"content": "Your rephrased bullet here."}}"""

BATCH_REWRITER_PROMPT = """You are an expert resume writer. Your task is to rephrase a batch of resume bullets to improve their impact, ensure they follow the STAR method, and maintain diversity in word choice.

Context: {context}

Bullets to rephrase:
{bullets_data}

Overused words in the original resume (AVOID these): {repeated_words}
Words used in other rephrased bullets (AVOID these to ensure variety): {accumulated_used_words}

Constraints:
- Provide exactly one rephrased version for each bullet ID provided.
- NEVER invent new facts, metrics, or technologies.
- Use a DIFFERENT and powerful action verb for each bullet in this batch.
- Ensure the rephrased bullets are concise and follow a result-oriented structure.
- If a bullet is already excellent, you can return it as-is or slightly polished.

Response Format:
Respond with ONLY a JSON object mapping bullet IDs to their new content.
Example:
{{
  "id_1": "Architected a scalable data pipeline...",
  "id_2": "Spearheaded cross-functional team of 10..."
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
