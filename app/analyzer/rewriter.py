import json
import re
from ..llm.protocol import LLMClient
from .prompts.rewriter_prompts import get_rewriter_prompt


async def rewrite_bullet(bullet: str, suggestion: str, llm_client: LLMClient) -> dict:
    prompt_template = get_rewriter_prompt()
    formatted_prompt = prompt_template.format(
        bullet=bullet,
        suggestion=suggestion,
    )

    try:
        response = await llm_client.ainvoke(formatted_prompt)
        text = response.strip()

        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = text

        json_str = json_str.replace('\n', ' ').replace('\r', '')
        result = json.loads(json_str)

        return result
    except Exception as e:
        return {
            "error": str(e),
            "content": f"{bullet} (Error generating rewrite)",
        }