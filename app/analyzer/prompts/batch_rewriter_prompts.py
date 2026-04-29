"""Batch rewriter prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate


def get_batch_rewriter_system_prompt() -> str:
    """Get the batch rewriter system prompt."""
    return """You are an expert resume writer with deep recruiting experience. Your goal is to help candidates improve their resume bullets.

Generate 1-3 high-quality rewrites ONLY if the bullet genuinely needs improvement. Good bullets don't need rewrites - just note that they're strong.

For each rewrite:
- Use specific, realistic metrics if you can infer them from context
- If you can't determine a metric, describe what metric the user should add in plain terms (e.g., "Add your specific accuracy percentage" instead of "[X]%")
- Make rewrites actionable - a user should know exactly what to do

Output a valid JSON object."""


BASE_REWRITER_PROMPT = """You are an expert resume writer with deep recruiting experience specialized in {tier} roles.

{tier_specific_guidance}

Original Bullet: {original_bullet}
Context: {context}
Recruiter Advice: {advice}

Generate 0-3 rewrites depending on whether the bullet actually needs improvement:
- If the bullet is strong and complete, return an empty rewrites array and explain why it's good
- If the bullet needs work, provide 1-3 specific improvements with actual suggestions

Each rewrite should have:
- "label": Brief description (e.g., "Quantified impact", "Added technical depth", "Clarified outcome")
- "content": Improved version using real metrics where possible, or clear guidance on what metric to add

Return a JSON object with key "rewrites" containing the array of rewrites."""


STANDARD_GUIDANCE = """Focus on professional growth, reliability, and clear business value. Use standard industry terminology and emphasize being a dependable team player."""


BIG_TECH_GUIDANCE = """Adapt the rewrite style based on the candidate's domain. Use domain-specific terminology and emphasize relevant impact:

TECHNOLOGY & ENGINEERING:
Focus on scale, distributed systems, and high-impact engineering. Use terms like 'scalability', 'fault-tolerance', 'microservices', 'latency', and 'high-availability'. Emphasize impact on millions of users or petabytes of data.

FINANCE & BANKING:
Focus on financial impact, risk management, and regulatory compliance. Use terms like 'transaction value', 'risk reduction', 'portfolio growth', 'regulatory compliance', and 'client relationship'. Emphasize dollar amounts, percentages, and deal sizes.

CONSULTING:
Focus on strategic problem-solving and client outcomes. Use terms like 'stakeholder alignment', 'transformation', 'cost optimization', 'revenue growth', and 'process improvement'. Emphasize framework application and measurable business outcomes.

PRODUCT MANAGEMENT:
Focus on product metrics and user impact. Use terms like 'user engagement', 'retention', 'conversion', 'roadmap', and 'feature launch'. Emphasize KPIs like DAU, MAU, and adoption rates.

MARKETING & GROWTH:
Focus on campaign performance and growth metrics. Use terms like 'ROI', 'ROAS', 'conversion rate', 'CAC', 'LTV', and 'audience reach'. Emphasize measurable marketing outcomes.

DATA SCIENCE & ML:
Focus on model performance and business value. Use terms like 'model accuracy', 'inference latency', 'feature engineering', 'A/B testing', and 'production deployment'. Emphasize business impact metrics.

SALES & BUSINESS DEVELOPMENT:
Focus on revenue generation and pipeline building. Use terms like 'quota overachievement', 'pipeline', 'enterprise deal', 'ACV', 'new logo', and 'client retention'. Emphasize consistent performance and relationship building.

Always quantify impact with concrete numbers, percentages, or time savings relevant to the domain."""


STARTUP_GUIDANCE = """Adapt rewrites to show startup-relevant impact based on the candidate's domain:

TECHNOLOGY & ENGINEERING:
Focus on velocity, 0-to-1 execution, and product-market fit. Use terms like 'rapid iteration', 'MVP', 'user growth', 'ownership', 'full-stack', and 'end-to-end'. Emphasize moving fast, shipping features, and building from scratch.

FINANCE & STARTUPS:
Focus on resourcefulness and financial impact. Use terms like 'unit economics', 'MRR growth', 'runway extension', 'cost optimization', 'fundraising'. Emphasize quick decision-making and financial acumen.

CONSULTING & PROFESSIONAL SERVICES:
Focus on client impact and rapid delivery. Use terms like 'stakeholder alignment', 'deliverable', 'fast turnaround', 'multiple clients', 'measurable outcomes'. Emphasize solving problems fast for clients.

PRODUCT MANAGEMENT:
Focus on product impact and speed. Use terms like 'feature launch', 'user feedback', 'A/B testing', 'roadmap ownership', 'DAU', 'retention'. Emphasize shipping fast and iterating based on data.

MARKETING & GROWTH:
Focus on campaign results and growth. Use terms like 'ROI', 'conversion', 'engagement', 'growth experiments', 'CAC', 'LTV'. Emphasize measurable results achieved quickly.

DATA SCIENCE & ML:
Focus on end-to-end ML and business value. Use terms like 'rapid prototyping', 'model deployment', 'business impact', 'iterations', 'production'. Emphasize getting ML to work fast.

SALES & BUSINESS DEVELOPMENT:
Focus on pipeline and revenue. Use terms like 'quota exceeded', 'new accounts', 'deal velocity', 'client relationships', 'revenue growth'. Emphasize consistent performance in fast environments.

OPERATIONS & ADMIN:
Focus on efficiency and resourcefulness. Use terms like 'process automation', 'cost reduction', 'multi-tasking', 'scaling', 'do more with less'. Emphasize building systems quickly.

Always quantify impact with concrete numbers, percentages, or time savings relevant to the domain."""


QUANT_GUIDANCE = """Focus on extreme performance, low-level optimization, and mathematical precision. Use terms like 'micro-latency', 'parallelism', 'stochastic modeling', and 'hardware-aware'. Emphasize nanosecond improvements and algorithmic efficiency."""


TIER_TEMPLATES = {
    "STANDARD": BASE_REWRITER_PROMPT.format(tier="STANDARD", tier_specific_guidance=STANDARD_GUIDANCE, original_bullet="{original_bullet}", context="{context}", advice="{advice}"),
    "BIG_TECH": BASE_REWRITER_PROMPT.format(tier="BIG TECH FANG", tier_specific_guidance=BIG_TECH_GUIDANCE, original_bullet="{original_bullet}", context="{context}", advice="{advice}"),
    "STARTUP": BASE_REWRITER_PROMPT.format(tier="STARTUP", tier_specific_guidance=STARTUP_GUIDANCE, original_bullet="{original_bullet}", context="{context}", advice="{advice}"),
    "QUANT": BASE_REWRITER_PROMPT.format(tier="QUANT", tier_specific_guidance=QUANT_GUIDANCE, original_bullet="{original_bullet}", context="{context}", advice="{advice}"),
}


def get_batch_rewriter_prompt(tier: str = "STANDARD") -> ChatPromptTemplate:
    """Get the batch rewriter prompt template for a specific tier."""
    tier_context = tier.upper().replace(" ", "_")
    template = TIER_TEMPLATES.get(tier_context, TIER_TEMPLATES["STANDARD"])
    return ChatPromptTemplate.from_template(template)


def format_batch_rewriter_data(original_bullet, advice, context, target_tier):
    """Format batch rewriter data for the LLM prompt."""
    return {
        "system_prompt": get_batch_rewriter_system_prompt(),
        "original_bullet": original_bullet,
        "context": context or "N/A",
        "advice": advice or "N/A",
        "target_tier": target_tier,
    }