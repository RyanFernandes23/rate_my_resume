import json
import re
from ..llm.client import llm


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


REWRITER_PROMPT = """You are a world-class executive resume writer who specializes in quant-heavy, Big Tech, and high-growth startup resumes.

Your task is to REWRITE a specific bullet point from a resume to address a critique and align with a specific career tier.

Career Tier Context:
- Standard Enterprise: Professional, clear, balanced metrics.
- Big Tech (FAAANG): High scale, complexity, ownership, data-driven outcomes.
- Early Stage Startup: Speed, multi-stack handling, zero-to-one impact, resourceful.
- Quant/Research: Technical depth, mathematical precision, rigor, performance optimization.

Input:
1. Original Bullet Point: The current text.
2. Suggestion: The specific critique from the analysis (e.g., "Add more metrics").
3. Target Tier: The desired career path.
4. Metric Hint: Suggested metric type to use (e.g., "[X]%", "[Y]k users").

Output Requirements:
Provide 3 distinct versions of the rewritten bullet:
1. "Action-Oriented": Focuses on strong lead verbs and ownership.
2. "Data-Driven": Focuses on quantifiable metrics and scale (KPIs, %, $, Users). Use the Metric Hint to guide your metrics.
3. "Technical/Concise": Focuses on specific tools and efficient phrasing.

Constraint: 
- Keep each bullet to 1-2 lines.
- Use strong action verbs (Architected, Spearheaded, Orchestrated).
- If the original bullet mentioned specific tech, preserve it.
- CRITICAL: Ensure the JSON is strictly valid. Do NOT use unescaped double quotes inside the "content" strings. Use single quotes if necessary. No trailing commas.

Return ONLY a JSON object:
{
    "versions": [
        {"label": "Action-Oriented", "content": "..."},
        {"label": "Data-Driven", "content": "..."},
        {"label": "Technical/Concise", "content": "..."}
    ]
}
"""


def rewrite_bullet(bullet: str, suggestion: str, target_tier: str) -> dict:
    metric_hint = _infer_metric_hint(bullet, suggestion)
    
    prompt = f"""{REWRITER_PROMPT}

Original Bullet: {bullet}
Critique to Address: {suggestion}
Target Tier: {target_tier}
Metric Hint: Use {metric_hint} as your primary metric placeholder

Return 3 optimized versions in valid JSON format."""

    try:
        response = llm.invoke(prompt)
        text = response.content.strip()

        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = text

        json_str = json_str.replace('\n', ' ').replace('\r', '')
        
        return json.loads(json_str)
    except Exception as e:
        try:
            return json.loads(json_str)
        except:
            return {
                "error": str(e),
                "versions": [
                    {"label": "Action-Oriented", "content": f"{bullet} (Error generating rewrite)"},
                    {"label": "Data-Driven", "content": f"{bullet} (Error generating rewrite)"},
                    {"label": "Technical/Concise", "content": f"{bullet} (Error generating rewrite)"}
                ]
            }
