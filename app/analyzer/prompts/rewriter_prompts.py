from langchain_core.prompts import ChatPromptTemplate

BASE_REWRITER_PROMPT = """You are a world-class executive resume writer who specializes in {tier} roles.
Your task is to REWRITE a specific bullet point from a resume to address a critique and align with the {tier} standards.

{tier_specific_guidance}

Input:
1. Original Bullet Point: {bullet}
2. Suggestion: {suggestion}
3. Metric Hint: {metric_hint}

Output Requirements:
Provide 3 distinct versions of the rewritten bullet which are easier and human-readable for recruiters:
1. "Action-Oriented": Focuses on strong lead verbs and ownership.
2. "Data-Driven": Focuses on quantifiable metrics and scale (KPIs, %, $, Users). Use the Metric Hint as a guide.
3. "Technical/Concise": Focuses on specific tools and efficient phrasing.

Constraint: 
- Keep each bullet to 1-2 lines.
- Preserve the key points/content mentioned in the original bullet.
- don't add any extra information or descriptions which are not present in the original bullet.
- Ensure the JSON is strictly valid.

Return ONLY a JSON object:
{{
    "versions": [
        {{"label": "Action-Oriented", "content": "..."}},
        {{"label": "Data-Driven", "content": "..."}},
        {{"label": "Technical/Concise", "content": "..."}}
    ]
}}"""

STANDARD_GUIDANCE = """- Focus on professional communication and clear results.
- Ensure the bullet follows the Action + Result pattern for general enterprise roles."""

BIG_TECH_GUIDANCE = """Adapt the rewrite based on the candidate's domain. Focus on the following based on field:

TECHNOLOGY & ENGINEERING:
- Use terms like 'distributed systems', 'microservices', 'high-availability', and 'latency'.
- Quantify impact on millions of users or large data systems.
- Highlight system design decisions, performance optimizations, and scale.

FINANCE & BANKING:
- Quantify financial impact (revenue, cost savings, deal values).
- Use terms like 'risk reduction', 'compliance', 'regulatory', 'transaction value'.
- Highlight deal pipeline, client relationships, or portfolio management.

CONSULTING:
- Use terms like 'stakeholder alignment', 'strategic framework', 'transformational'.
- Quantify business impact (cost reduction %, revenue growth, efficiency gains).
- Highlight client outcomes and C-level engagement.

PRODUCT MANAGEMENT:
- Connect to KPIs: DAU, MAU, retention, conversion, user engagement.
- Use terms like 'roadmap', 'feature launch', 'user research', 'A/B testing'.
- Highlight cross-functional leadership and product strategy.

MARKETING & GROWTH:
- Use terms like 'campaign ROI', 'conversion rate', 'engagement', 'reach'.
- Quantify marketing metrics (CTR, ROAS, CAC, LTV).
- Highlight channel expertise and growth experiments.

DATA SCIENCE & ML:
- Use terms like 'model accuracy', 'inference latency', 'production deployment'.
- Quantify model performance improvements or business impact.
- Highlight end-to-end ML pipelines and MLOps.

SALES & BUSINESS DEVELOPMENT:
- Use terms like 'quota overachievement', 'pipeline', 'enterprise deals', 'ACV'.
- Quantify sales performance and revenue generation.
- Highlight strategic partnerships and client relationships.

OPERATIONS & SUPPLY CHAIN:
- Use terms like 'process efficiency', 'cost reduction', 'vendor management'.
- Quantify operational improvements (time saved, error reduction, cost savings).
- Highlight Lean Six Sigma, ERP implementations, or scaling operations.

Always emphasize measurable, quantifiable outcomes relevant to the specific domain."""

STARTUP_GUIDANCE = """Adapt rewrites to show startup-relevant impact based on the candidate's domain:

TECHNOLOGY & ENGINEERING:
- Focus on agility, ownership, and 0-to-1 building.
- Use terms like 'rapid iteration', 'MVP', 'end-to-end ownership', 'full-stack'.
- Emphasize user impact, feature launches, and fast delivery.

FINANCE & STARTUPS:
- Focus on resourcefulness and speed.
- Use terms like 'unit economics', 'MRR growth', 'runway extension', 'cost optimization'.
- Emphasize financial impact and quick decision-making.

CONSULTING & PROFESSIONAL SERVICES:
- Focus on client impact and rapid problem-solving.
- Use terms like 'stakeholder alignment', 'deliverable', 'fast turnaround', 'multiple clients'.
- Emphasize measurable outcomes and client satisfaction.

PRODUCT MANAGEMENT:
- Focus on product impact and user-centric results.
- Use terms like 'feature launch', 'user feedback', 'A/B testing', 'roadmap ownership'.
- Emphasize metrics (DAU, retention, conversion) and speed to market.

MARKETING & GROWTH:
- Focus on campaign results and growth metrics.
- Use terms like 'ROI', 'conversion', 'engagement', 'growth experiments'.
- Emphasize measurable marketing impact quickly achieved.

DATA SCIENCE & ML:
- Focus on end-to-end ML and business impact.
- Use terms like 'rapid prototyping', 'model deployment', 'business value', 'iterations'.
- Emphasize getting ML to production fast.

SALES & BUSINESS DEVELOPMENT:
- Focus on pipeline and revenue generation.
- Use terms like 'quota exceeded', 'new accounts', 'deal velocity', 'client relationships'.
- Emphasize consistent performance and quick wins.

OPERATIONS & ADMIN:
- Focus on efficiency and resourcefulness.
- Use terms like 'process automation', 'cost reduction', 'multi-tasking', 'scaling'.
- Emphasize doing more with less.

Always quantify impact with concrete numbers, percentages, or time savings relevant to the domain."""

QUANT_GUIDANCE = """- Focus on technical precision and algorithmic efficiency.
- Mention low-level optimizations, mathematical rigor, and micro-latency performance."""

TIER_TEMPLATES = {
    "STANDARD": BASE_REWRITER_PROMPT.format(tier="STANDARD", tier_specific_guidance=STANDARD_GUIDANCE, bullet="{bullet}", suggestion="{suggestion}", metric_hint="{metric_hint}"),
    "BIG_TECH": BASE_REWRITER_PROMPT.format(tier="BIG TECH FANG", tier_specific_guidance=BIG_TECH_GUIDANCE, bullet="{bullet}", suggestion="{suggestion}", metric_hint="{metric_hint}"),
    "STARTUP": BASE_REWRITER_PROMPT.format(tier="STARTUP", tier_specific_guidance=STARTUP_GUIDANCE, bullet="{bullet}", suggestion="{suggestion}", metric_hint="{metric_hint}"),
    "QUANT": BASE_REWRITER_PROMPT.format(tier="QUANT", tier_specific_guidance=QUANT_GUIDANCE, bullet="{bullet}", suggestion="{suggestion}", metric_hint="{metric_hint}"),
}


def get_rewriter_prompt(tier: str = "STANDARD") -> ChatPromptTemplate:
    """Get the rewriter prompt for a specific tier."""
    tier_context = tier.upper().replace(" ", "_")
    template = TIER_TEMPLATES.get(tier_context, TIER_TEMPLATES["STANDARD"])
    return ChatPromptTemplate.from_template(template)
