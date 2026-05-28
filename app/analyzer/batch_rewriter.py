"""Batch rewriter using LangChain and externalized prompts."""
import asyncio
import json
import logging
import re
from typing import Any
from ..llm.protocol import LLMClient
from .prompts.batch_rewriter_prompts import get_batch_rewriter_prompt, format_multi_bullet_data
from .repetition_checker import CORE_STOPWORDS

logger = logging.getLogger(__name__)

# Pattern to find meaningful words (4+ chars, not core stopwords)
_SIGNIFICANT_WORD_RE = re.compile(r"\b[a-z]{4,}\b")


def _clean_json_response(content: str) -> str:
    """Extract the first JSON object from LLM response, ignoring markdown fences and preamble text."""
    text = content.strip()

    fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()

    brace_match = re.search(r'\{.*\}', text, re.DOTALL)
    if brace_match:
        return brace_match.group(0).strip()

    return text


def _extract_significant_words(text: str) -> set[str]:
    """Extract words that are likely to be repetitive and should be tracked (e.g. action verbs)."""
    words = {m.group().lower() for m in _SIGNIFICANT_WORD_RE.finditer(text.lower())}
    return words - CORE_STOPWORDS


async def batch_rewrite_suggestions(
    actionable_suggestions: list[dict[str, Any]], 
    llm_client: LLMClient, 
    accumulated_used_words: set[str] | None = None
) -> dict[str, dict[str, str]]:
    """
    Generate rephrased bullets in batches to ensure diversity and efficiency.

    accumulated_used_words: a shared set of significant words already used in previous
    batches. Updated in-place as batches are processed.
    """
    if not actionable_suggestions:
        return {}

    if accumulated_used_words is None:
        accumulated_used_words = set()

    # Assign unique IDs for mapping LLM response back to suggestions
    for i, sug in enumerate(actionable_suggestions):
        sug["id"] = f"b{i}"

    rewrites = {}
    _lock = asyncio.Lock()

    # Process in batches of 5 to keep context manageable and ensure variety
    BATCH_SIZE = 5
    batches = [actionable_suggestions[i : i + BATCH_SIZE] for i in range(0, len(actionable_suggestions), BATCH_SIZE)]

    async def process_batch(batch_items):
        nonlocal accumulated_used_words

        # Collect repeated words from all bullets in this batch
        batch_repeated = set()
        for item in batch_items:
            for word in item.get("repeated_words", []):
                batch_repeated.add(word.lower())

        async with _lock:
            used_snapshot = sorted(list(accumulated_used_words))

        try:
            prompt = get_batch_rewriter_prompt(is_batch=True)
            # Use the first item's context as a proxy for the batch (usually the same section)
            context = batch_items[0].get("context", "Resume Experience/Projects")

            formatted_data = format_multi_bullet_data(
                bullets=batch_items,
                context=context,
                repeated_words=list(batch_repeated),
                accumulated_used_words=used_snapshot
            )

            formatted_prompt = prompt.format(**formatted_data)
            response = await llm_client.ainvoke(formatted_prompt)
            json_str = _clean_json_response(response)

            try:
                batch_results = json.loads(json_str)
                if not isinstance(batch_results, dict):
                    logger.error(f"Batch rewriter returned non-dict JSON: {type(batch_results)}")
                    return

                new_significant_words = set()
                for item in batch_items:
                    bullet_id = item["id"]
                    content = batch_results.get(bullet_id)
                    if content:
                        key = f"{item['section']}__{item['entry_index']}__{item['bullet_index']}"
                        rewrites[key] = {"label": "Rephrased", "content": content}
                        new_significant_words.update(_extract_significant_words(content))

                async with _lock:
                    accumulated_used_words.update(new_significant_words)

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON batch response: {e}\nResponse: {json_str[:200]}")

        except Exception as e:
            logger.error(f"Error in batch rewrite: {e}")

    # Process batches with some concurrency but respect the shared set
    semaphore = asyncio.Semaphore(2)
    async def throttled_batch(b):
        async with semaphore:
            await process_batch(b)

    tasks = [throttled_batch(b) for b in batches]
    await asyncio.gather(*tasks)

    return rewrites