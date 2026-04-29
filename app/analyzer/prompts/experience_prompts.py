"""Experience analyzer prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate


BASE_EXPERIENCE_PROMPT = """You are a senior recruiter and resume strategist specialized in {tier} roles. 
Analyze each experience entry below and provide a comprehensive assessment.

For each experience entry, your response must include:
1. "score": A score from 0-25 based on {tier} standards.(this score should be evaluate based on below bullets)
2. "star_score": A score from 0-10 based on STAR principle usage.
3. "star_reasoning": Brief explanation of why this star_score was given.
4. "good_things": List of 1-3 specific strengths found in the bullets.
5. "recommendation": Either "keep" or "revise".
6. "suggestions": A list of bullet-specific suggestions. Each suggestion should have:
    - "bullet_index": The index of the bullet.
    - "original_bullet": The original text.
    - "context": Why this matters for {tier}.
    - "advice": Specific, actionable feedback about this bullet. Be direct - if the bullet is good, say so. If it needs work, explain exactly what's missing and why it matters.
    - "rewrites": (OPTIONAL) Only include if the bullet genuinely needs improvement. Each rewrite should have:
      - "label": A short description of the rewrite approach (e.g., "Quantified impact", "Added technical depth", "Clarified outcome").
      - "content": A rewritten version that actually improves the bullet. Use REAL metrics if you can infer them from context, otherwise describe what metric the user should add without using placeholder tokens.

{tier_specific_guidance}

SCORING_RUBRIC (STRICT):
- 0-12 (POOR): Vague bullets, "responsible for" phrasing, ZERO metrics, or irrelevant tech stack.
- 13-18 (AVERAGE): Clear tasks but missing the 'Result' in STAR. Basic metrics used but impact feels small.
- 19-22 (STRONG): Strong STAR usage, clear quantifiable impact, and deep technical mastery relevant to {tier}.
- 23-25 (EXPERT): Exceptional impact (e.g., $1M+ saved, 90%+ optimization, led teams of 10+). Rare technical achievement.

General Guidelines:
- BE CRITICAL. A 25/25 should be extremely rare, reserved for "Big Tech" level lead engineers or equivalent.
- PENALIZE HEAVILY (-5 to -10 points) if bullets lack quantifiable metrics (%, $, numbers).
- If bullets lack metrics, provide concrete advice on WHAT metric would be relevant (e.g., "Add specific metrics like percentage improvement, time saved, or users impacted").
- Mention missing TECHNICAL DEPTH relevant to {tier}.
- Never fabricate numbers. If you can't infer a realistic metric, simply state what type of metric the user should add (e.g., "Add performance improvement percentage" instead of "[X]%").

IMPORTANT: Output MUST be a valid JSON object with a key "entries" which is a list of objects, one for each experience entry.

Experience Data:
{experience_data}

Return the JSON analysis."""


STANDARD_GUIDANCE = """Focus on:
- Clear ownership: Use "I" vs "we" implicitly by starting with strong verbs.
- Direct outcomes: What was the result of the task? (e.g., 'reduced manual work by 5 hours/week').
- Professional framing: Avoid jargon that only makes sense within one company.
- Completeness: Ensure the bullet follows the Action + Result pattern."""

BIG_TECH_GUIDANCE = """Focus on scale, impact, and domain-relevant achievements. Adapt based on the candidate's field:

TECHNOLOGY & ENGINEERING:
- Scale & Complexity: Use terms like 'distributed systems', 'microservices', 'millions of users', 'Petabytes of data'.
- System Design: Highlight trade-offs made (e.g., 'Optimized for read-heavy workload by implementing caching').
- Latency & Throughput: Quantify performance improvements in ms or RPS.
- Cross-functional Impact: Mention collaborating with multiple teams or influencing org-wide standards.
- Operational Excellence: Mention monitoring, CI/CD, or reducing on-call toil.

FINANCE & BANKING:
- Deal Value: Mention transaction sizes, funding rounds, or portfolio value (e.g., '$50M+ in processed transactions').
- Client Impact: Highlight relationships with institutional clients, banks, or investors.
- Regulatory Success: Mention navigating complex compliance (SEC, FINRA, Basel III).
- Risk Reduction: Quantify how your work reduced risk or improved compliance.
- Revenue Impact: State revenue generated, cost savings, or efficiency gains.

CONSULTING:
- Problem-Solving Scale: Mention team size, project scope, or client Fortune 500 status.
- Framework Application: Reference strategic frameworks used (BCG, McKinsey, Bain).
- Client Outcomes: Highlight measurable outcomes (cost reduction %, revenue growth, efficiency gains).
- Stakeholder Management: Mention C-level presentations or board communications.
- Cross-industry Experience: Show versatility across sectors.

PRODUCT MANAGEMENT:
- Product Launch: Mention shipping features used by thousands/millions of users.
- Metrics-Driven: Include KPIs like DAU, MAU, retention, conversion rates.
- Roadmap Ownership: Show strategic prioritization and alignment with business goals.
- Cross-functional Leadership: Highlight working with engineering, design, marketing.
- User Research: Mention conducting user interviews, A/B tests, or feedback loops.

MARKETING & GROWTH:
- Campaign ROI: Quantify campaign performance (ROI, ROAS, conversion rates).
- Audience Scale: Mention reach, impressions, or follower growth.
- Channel Expertise: Highlight specific channels (SEO, paid, social, email).
- Revenue Attribution: Connect marketing efforts to pipeline or revenue.
- Brand Impact: Mention brand awareness metrics or sentiment improvements.

DATA SCIENCE & ML:
- Model Impact: Mention accuracy improvements, prediction accuracy, or business impact.
- Scale of Data: Reference dataset sizes (millions of rows, TB/PB scale).
- Algorithm Sophistication: Highlight deep learning, NLP, computer vision, or reinforcement learning.
- Production ML: Mention MLOps, model deployment, or real-time inference.
- Business Value: Connect models to revenue, cost savings, or user engagement.

SALES & BUSINESS DEVELOPMENT:
- Quota Achievement: Show consistent overachievement (120%+ of quota).
- Deal Size: Mention enterprise deals, average contract value, or key wins.
- Pipeline Generation: Highlight pipeline built or new accounts opened.
- Client Relationships: Mention strategic accounts or long-term relationships.
- Revenue Growth: State YoY growth, new revenue streams, or market expansion.

OPERATIONS & SUPPLY CHAIN:
- Process Efficiency: Quantify time saved, cost reduced, or error rates decreased.
- Vendor Management: Highlight negotiations, cost savings, or supplier relationships.
- Scaling Operations: Show handling growth in volume, teams, or geographies.
- KPI Management: Mention operational metrics tracked and improved.
- Lean/Six Sigma: Reference process improvement methodologies.

Quantify impact using percentages, dollar amounts, or time saved wherever possible."""

STARTUP_GUIDANCE = """Focus on versatility, ownership, and impact in resource-constrained environments. Adapt based on the candidate's domain:

TECHNOLOGY & ENGINEERING:
- 0 to 1 Building: Mention launching products or features from scratch.
- Speed of Execution: Highlight rapid prototyping and deployment cycles.
- Customer/Product Impact: How did your work affect user growth, retention, or revenue?
- Ambiguity: Show how you defined requirements in a fast-paced environment.
- Full-stack/Versatility: Mention wearing multiple hats (e.g., 'Managed AWS infra while developing frontend').

FINANCE & STARTUPS:
- Resourcefulness: Work with limited budget, fast decisions, lean operations.
- Fundraising: Mention involvement in pitch prep, investor meetings, or financial planning.
- Growth Metrics: Show understanding of MRR, ARR, runway, burn rate.
- Multiple Roles: Wore many hats - from accounting to analytics to ops.
- Speed to Revenue: Closed deals, built models, or generated revenue quickly.

CONSULTING & PROFESSIONAL SERVICES:
- Client Impact: Measurable outcomes for diverse clients quickly.
- Rapid Learning: Adapted to new industries or domains fast.
- Workshop Facilitation: Led sessions, designed frameworks, drove decisions.
- Problem Solving: Ill-structured problems, ambiguous client needs.
- Communication: Presentation to C-suite, stakeholder management.

PRODUCT MANAGEMENT:
- Feature Ownership: Shipped features from idea to launch fast.
- User-Centric: Used data and user feedback to drive decisions.
- Cross-functional: Coordinated with engineering, design, marketing simultaneously.
- Metrics-Driven: Tracked and improved KPIs (DAU, retention, conversion).
- Roadmap: Balanced speed with strategic alignment.

MARKETING & GROWTH:
- Campaign Execution: Ran multiple campaigns simultaneously, quick iterations.
- Growth Experiments: A/B testing, SEO quick wins, viral loops.
- Content Creation: Created blogs, videos, social media at speed.
- Channel Proficiency: Handled paid, organic, email, social quickly.
- Measurable Results: ROAS, CTR, engagement metrics achieved fast.

DATA SCIENCE & ML:
- Quick Prototyping: Built ML models fast with minimal resources.
- End-to-End: Handled data, modeling, deployment single-handedly.
- Business Impact: Connected ML work to revenue or cost savings quickly.
- Experimentation: Rapid A/B testing, quick iterations on models.
- Tool Diversity: Used multiple tools to get things done fast.

SALES & BUSINESS DEVELOPMENT:
- Pipeline Building: Generated leads and opportunities quickly.
- Deal Velocity: Closed deals fast, managed multiple prospects.
- Relationship Building: Built rapport quickly, demos, follow-ups.
- Revenue Impact: Contributed directly to revenue early.
- Adaptability: Pivoted approach based on market feedback fast.

OPERATIONS & ADMIN:
- Process Creation: Built processes from scratch with limited resources.
- Multi-tasking: Handled diverse responsibilities simultaneously.
- Automation: Automated manual tasks to save time and money.
- Vendor Management: Negotiated quickly, managed relationships.
- Scalability: Prepared operations for growth efficiently.

Quantify impact using numbers, percentages, or time saved. Show ownership and end-to-end involvement."""

QUANT_GUIDANCE = """Focus on:
- Micro-latency: Quantify performance in microseconds or nanoseconds.
- Technical Depth: Mention low-level memory management, lock-free data structures, or kernel-level optimizations.
- Mathematical Rigor: Highlight algorithmic complexity analysis or statistical modeling.
- Reliability: Focus on zero-downtime and extreme correctness in high-stakes environments.
- Languages: Emphasize modern C++, Rust, or high-performance Python (Cython/NumPy)."""

TIER_TEMPLATES = {
    "STANDARD": BASE_EXPERIENCE_PROMPT.format(tier="STANDARD", tier_specific_guidance=STANDARD_GUIDANCE, experience_data="{experience_data}"),
    "BIG_TECH": BASE_EXPERIENCE_PROMPT.format(tier="BIG TECH FANG", tier_specific_guidance=BIG_TECH_GUIDANCE, experience_data="{experience_data}"),
    "STARTUP": BASE_EXPERIENCE_PROMPT.format(tier="STARTUP", tier_specific_guidance=STARTUP_GUIDANCE, experience_data="{experience_data}"),
    "QUANT": BASE_EXPERIENCE_PROMPT.format(tier="QUANT", tier_specific_guidance=QUANT_GUIDANCE, experience_data="{experience_data}"),
}


def get_experience_prompt(tier: str) -> ChatPromptTemplate:
    """Get the experience analysis prompt for a specific tier."""
    tier_context = tier.upper().replace(" ", "_")
    
    # Fallback to standard if tier not found
    template = TIER_TEMPLATES.get(tier_context, TIER_TEMPLATES["STANDARD"])
    
    return ChatPromptTemplate.from_template(template)


def format_experience_data(experience_entries):
    """Format experience entries for the LLM prompt."""
    exp_data = []
    for i, exp in enumerate(experience_entries):
        exp_data.append({
            "entry_index": i,
            "company": exp.company,
            "title": exp.title,
            "bullets": {idx: bullet for idx, bullet in enumerate(exp.descriptions or [])},
        })
    import json
    return json.dumps(exp_data, indent=2)
