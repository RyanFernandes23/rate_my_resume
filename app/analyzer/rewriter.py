import json
import re
from ..llm.client import llm
from .prompts.rewriter_prompts import get_rewriter_prompt


def _suggest_metric_type(bullet: str, suggestion: str) -> str:
    """Suggest what type of metric would be relevant based on context."""
    combined = (bullet + " " + suggestion).lower()
    
    if any(k in combined for k in ["improve", "increase", "increase", "optimize", "enhance"]):
        return "Add a specific percentage or numerical improvement (e.g., 'improved by X%')"
    elif any(k in combined for k in ["reduce", "decrease", "save", "cut"]):
        return "Add a specific reduction amount (e.g., 'reduced by X%' or 'saved X hours')"
    elif any(k in combined for k in ["scale", "users", "customers", "requests", "queries"]):
        return "Add scale metrics (e.g., number of users, requests per day)"
    elif any(k in combined for k in ["accuracy", "precision", "performance"]):
        return "Add performance metrics (e.g., accuracy percentage, latency in ms)"
    elif any(k in combined for k in ["cost", "revenue", "budget"]):
        return "Add financial metrics (e.g., dollar amount, cost savings)"
    elif any(k in combined for k in ["time", "speed", "faster"]):
        return "Add time-based metrics (e.g., hours saved, time reduction)"
    else:
        return "Add quantifiable metrics relevant to this work"


def rewrite_bullet(bullet: str, suggestion: str) -> dict:
    metric_suggestion = _suggest_metric_type(bullet, suggestion)
    
    prompt_template = get_rewriter_prompt()
    formatted_prompt = prompt_template.format(
        bullet=bullet,
        suggestion=suggestion,
        metric_suggestion=metric_suggestion
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
                {"label": "Improved", "content": f"{bullet} (Error generating rewrite)"}
            ]
        }