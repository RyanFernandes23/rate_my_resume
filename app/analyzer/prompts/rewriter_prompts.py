from langchain_core.prompts import ChatPromptTemplate

ENTERPRISE_GUIDANCE = """Adapt the rewrite based on the candidate's domain with professional enterprise standards. Focus on the following based on field:

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

BASE_REWRITER_PROMPT = """You are a world-class executive resume writer who specializes in professional enterprise roles.
Your task is to improve resume bullets when needed, based on recruiter feedback.

Adapt the rewrite based on the candidate's domain with professional enterprise standards. Focus on the following based on field:

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

Always emphasize measurable, quantifiable outcomes relevant to the specific domain.

Input:
1. Original Bullet Point: {{bullet}}
2. Suggestion: {{suggestion}}
3. Metric Guidance: {{metric_suggestion}}

Output:
- If the bullet is already strong and complete, just note it's good
- If it needs improvement, provide 1-2 improved versions that address the suggestion
- Use real metrics where you can infer them, otherwise describe what metric to add
- Don't use placeholder tokens like [X]% - instead say what kind of metric to add

Keep bullets concise (1-2 lines). Return a JSON object with key "versions"."""


def get_rewriter_prompt(tier: str = None) -> ChatPromptTemplate:
    """Get the rewriter prompt."""
    return ChatPromptTemplate.from_template(BASE_REWRITER_PROMPT)
