"""Batch rewriter using LangChain and externalized prompts."""
import re
import json
import logging
import time
from app.llm import _wait_for_rate_limit, _is_rate_limit_error
from app.llm.client import llm
from .prompts.batch_rewriter_prompts import get_batch_rewriter_prompt, format_batch_rewriter_data

logger = logging.getLogger(__name__)


def _extract_suggestion_id(suggestion_key: str) -> str:
    """Extract the numeric ID from a suggestion key like '0_1_2'."""
    parts = suggestion_key.split("__")
    if len(parts) >= 3:
        return parts[2]
    return suggestion_key


def _clean_json_response(content: str) -> str:
    """Clean markdown and extract JSON from LLM response."""
    json_str = content.strip()
    if json_str.startswith("```json"):
        json_str = json_str[7:]
    elif json_str.startswith("```\njson"):
        json_str = json_str[8:]
    elif json_str.startswith("```"):
        json_str = json_str[3:]
    if json_str.endswith("```"):
        json_str = json_str[:-3]
    return json_str.strip()


def _parse_rewrites_from_response(json_str: str, suggestion_key: str):
    """Parse rewrite options from LLM JSON response."""
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from batch rewriter: {e}")
        logger.error(f"Response was: {json_str[:500]}")
        return []

    rewrites = []
    label_map = {
        "action_oriented": "Action-Oriented",
        "data_driven": "Data-Driven",
        "leadership_impact": "Leadership/Impact",
    }

    for key, label in label_map.items():
        if key in data:
            item = data[key]
            if isinstance(item, dict) and "content" in item:
                rewrites.append({
                    "label": item.get("label", label),
                    "content": item["content"],
                })
            elif isinstance(item, str):
                rewrites.append({
                    "label": label,
                    "content": item,
                })

    return rewrites


def batch_rewrite_suggestions(actionable_suggestions, tier: str = "STANDARD"):
    """Generate rewrite options for multiple suggestions using LangChain."""
    rewrites = {}

    for sug in actionable_suggestions:
        section_key = sug["section"]
        entry_idx = sug["entry_index"]
        bullet_idx = sug["bullet_index"]
        suggestion_key = f"{section_key}__{entry_idx}__{bullet_idx}"

        # Rate limit handling
        _wait_for_rate_limit()

        try:
            prompt = get_batch_rewriter_prompt(tier)
            formatted_data = format_batch_rewriter_data(
                original_bullet=sug["bullet"],
                advice=sug.get("advice", ""),
                context=sug.get("context", ""),
                target_tier=tier,
            )
            formatted_prompt = prompt.format(**formatted_data)

            response = llm.invoke(formatted_prompt)
            json_str = _clean_json_response(response.content)

            parsed_rewrites = _parse_rewrites_from_response(json_str, suggestion_key)
            if parsed_rewrites:
                rewrites[suggestion_key] = parsed_rewrites
            else:
                logger.warning(f"No rewrites generated for {suggestion_key}")

            # Small delay to avoid rate limits
            time.sleep(0.5)

        except Exception as e:
            logger.error(f"Error generating rewrites for {suggestion_key}: {e}")
            # Provide fallback rewrites
            rewrites[suggestion_key] = [
                {
                    "label": "Action-Oriented",
                    "content": f"Spearheaded initiative that improved {sug['bullet'][:50]}... [X]% efficiency",
                },
                {
                    "label": "Data-Driven",
                    "content": f"Optimized process achieving [X]% improvement in {sug['bullet'][:40]}...",
                },
                {
                    "label": "Leadership/Impact",
                    "content": f"Led cross-functional team to enhance {sug['bullet'][:50]}... serving [Y]k users",
                },
            ]

    return rewrites
