"""Batch rewriter using LangChain and externalized prompts."""
import asyncio
import json
import logging
from app.llm import llm
from .prompts.batch_rewriter_prompts import get_batch_rewriter_prompt, format_batch_rewriter_data

logger = logging.getLogger(__name__)


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

    # Handle new format: {"rewrites": [{"label": "...", "content": "..."}, ...]}
    if "rewrites" in data:
        rewrites_list = data["rewrites"]
        if isinstance(rewrites_list, list):
            for item in rewrites_list:
                if isinstance(item, dict) and "content" in item:
                    rewrites.append({
                        "label": item.get("label", "Improved"),
                        "content": item["content"],
                    })

    # Handle old format for backward compatibility
    if not rewrites:
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


async def batch_rewrite_suggestions(actionable_suggestions):
    """Generate rewrite options for multiple suggestions in parallel using LangChain."""
    rewrites = {}
    
    async def process_single_suggestion(sug):
        section_key = sug["section"]
        entry_idx = sug["entry_index"]
        bullet_idx = sug["bullet_index"]
        suggestion_key = f"{section_key}__{entry_idx}__{bullet_idx}"

        try:
            prompt = get_batch_rewriter_prompt()
            formatted_data = format_batch_rewriter_data(
                original_bullet=sug["bullet"],
                advice=sug.get("advice", ""),
                context=sug.get("context", ""),
            )
            formatted_prompt = prompt.format(**formatted_data)

            response = await llm.ainvoke(formatted_prompt)
            json_str = _clean_json_response(response.content)

            parsed_rewrites = _parse_rewrites_from_response(json_str, suggestion_key)
            if parsed_rewrites:
                return suggestion_key, parsed_rewrites
            else:
                logger.warning(f"No rewrites generated for {suggestion_key}")
                return suggestion_key, []

        except Exception as e:
            logger.error(f"Error generating rewrites for {suggestion_key}: {e}")
            return suggestion_key, [
                {
                    "label": "Improved",
                    "content": "Consider revising this bullet to add specific metrics. Add details about the impact of your work.",
                },
            ]

    # Create tasks for all suggestions
    tasks = [process_single_suggestion(sug) for sug in actionable_suggestions]
    
    if not tasks:
        return {}
        
    # Run all tasks in parallel
    results = await asyncio.gather(*tasks)
    
    # Collate results
    for key, val in results:
        if val:
            rewrites[key] = val

    return rewrites