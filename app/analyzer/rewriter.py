import json
import re
from ..llm.client import llm
from .prompts.rewriter_prompts import get_rewriter_prompt


METRIC_HINTS = {
    "improve": "[X]%",
    "reduce": "[X]%",
    "increase": "[X]%",
    "decrease": "[X]%",
    "users": "[Y]k users",
    "queries": "[Y]k queries/day",
    "requests": "[Y]k requests/day",
    "accuracy": "[X]%",
    "latency": "[Y]ms",
    "throughput": "[X]%",
    "performance": "[X]%",
    "speed": "[X]%",
    "time": "[Y] hours",
    "cost": "$[X]",
    "revenue": "$[Y]k",
    "memory": "[Y]GB",
    "gpu": "[Z] GPUs",
}


def _infer_metric_hint(bullet: str, suggestion: str) -> str:
    """Infer the most relevant metric placeholder based on context."""
    combined = (bullet + " " + suggestion).lower()
    for keyword, placeholder in METRIC_HINTS.items():
        if keyword in combined:
            return placeholder
    return "[X]%"


def rewrite_bullet(bullet: str, suggestion: str, target_tier: str) -> dict:
    metric_hint = _infer_metric_hint(bullet, suggestion)
    
    prompt_template = get_rewriter_prompt(target_tier)
    formatted_prompt = prompt_template.format(
        bullet=bullet,
        suggestion=suggestion,
        metric_hint=metric_hint
    )

    try:
        response = llm.invoke(formatted_prompt)
        text = response.content.strip()

        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = text

        json_str = json_str.replace('\n', ' ').replace('\r', '')
        
        return json.loads(json_str)
    except Exception as e:
        return {
            "error": str(e),
            "versions": [
                {"label": "Action-Oriented", "content": f"{bullet} (Error generating rewrite)"},
                {"label": "Data-Driven", "content": f"{bullet} (Error generating rewrite)"},
                {"label": "Technical/Concise", "content": f"{bullet} (Error generating rewrite)"}
            ]
        }
