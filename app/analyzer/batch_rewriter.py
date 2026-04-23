import re
import json
import logging
import time
from app.llm import _wait_for_rate_limit, _is_rate_limit_error
from app.llm.client import llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert resume writer with deep recruiting experience. For each original bullet, generate exactly 3 STAR-based rewrite alternatives using placeholders for missing metrics.

IMPORTANT: Never fabricate specific numbers—use [X], [Y], [Z] placeholders unless the original bullet already contains a number.

Output ONLY a valid JSON object where keys are the suggestion IDs and values are arrays of objects with 'label' and 'content'."""

PROMPT_TEMPLATE = """{system_prompt}

Use the STAR framework (Situation, Task, Action, Result) and these strict rules for each rewrite style:

1. **Action-Oriented** (STAR emphasis: Situation & Action)
   - Start with a strong, unique action verb (Engineered, Architected, Spearheaded, Optimized, Accelerated).
   - Describe the Situation/Problem briefly and the Action taken.
   - End with a placeholder result tied directly to the action (e.g., "reducing [X]% manual effort" or "boosting [Y]% throughput").
   - Never use fake numbers; use [X]%, [Y]k, [Z] GPUs placeholders.
   - Keep to one sentence, 15-25 words.

2. **Data-Driven** (STAR emphasis: Result)
   - Start with a strong action verb.
   - Combine the action with a quantifiable outcome using placeholders, then explicitly link it to a business/engineering outcome.
   - Example: "Implemented [technique] achieving [X]% accuracy and [Y]% faster training, enabling deployment on [Z] GPUs with [A]% cost reduction."
   - If the original bullet already contains a real number, keep it and add placeholders for missing context.
   - 20-30 words, structure: Action → Metric → Impact.

3. **Technical/Concise** (STAR emphasis: Task & Action, ATS-friendly)
   - A tight, keyword-rich sentence under 18 words.
   - Include tools, techniques, and a placeholder metric (e.g., "Built ViT with PyTorch, achieving [X]% accuracy").
   - No fluff; every word earns its place.
   - Start with a verb.

General rules:
- Always use placeholders [X], [Y], [Z] for any number not present in the original bullet.
- Do NOT invent specific numbers; use placeholders.
- Highlight problem-solving, technical depth, and scale wherever possible.
- All versions must be truthful – if the original bullet has a specific metric, you may reuse it and add placeholders for further impacts.
- Keep language professional yet dynamic.

Here are the original bullets and their AI-generated suggestions:

{suggestions}

Return ONLY a JSON object. Example format:
{{
  "experience__0__0": [
    {{"label": "Action-Oriented", "content": "..."}},
    {{"label": "Data-Driven", "content": "..."}},
    {{"label": "Technical/Concise", "content": "..."}}
  ]
}}
"""


def batch_rewrite_suggestions(suggestions: list[dict]) -> dict:
    """
    suggestions: [
        {
            "section": "experience",
            "entry_index": 0,
            "bullet_index": 0,
            "bullet": "original bullet text",
            "suggestion": "full suggestion string (may contain quoted original)"
        },
        ...
    ]
    Returns dict like { "experience__0__0": [ { "label": "...", "content": "..." }, ... ], ... }
    Key format: "{section}__{entry_index}__{bullet_index}"
    """
    if not suggestions:
        return {}

    suggestions_text = ""
    for s in suggestions:
        sid = f"{s['section']}__{s['entry_index']}__{s['bullet_index']}"
        suggestions_text += f"ID: {sid}\n"
        suggestions_text += f"Original: {s['bullet']}\n"
        suggestions_text += f"Suggestion: {s['suggestion']}\n\n"

    prompt = PROMPT_TEMPLATE.format(
        system_prompt=SYSTEM_PROMPT,
        suggestions=suggestions_text
    )

    _wait_for_rate_limit()

    max_retries = 3
    base_delay = 10

    for attempt in range(max_retries):
        try:
            response = llm.invoke(prompt)
            json_str = response.content.strip()

            json_str = json_str.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            elif json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            json_str = json_str.strip()

            result = json.loads(json_str)
            if not isinstance(result, dict):
                logger.warning("LLM response is not a dict")
                return {}
            return result

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from LLM: {e}")
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2**attempt))
                continue
            return {}
        except Exception as e:
            if _is_rate_limit_error(e) and attempt < max_retries - 1:
                wait_time = base_delay * (2**attempt) * 2
                logger.warning(f"Rate limited. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            logger.error(f"Error in batch rewrite: {e}")
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2**attempt))
                continue
            return {}

    return {}