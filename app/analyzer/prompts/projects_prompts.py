"""Projects analyzer prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate


BASE_PROJECTS_PROMPT = """You are a senior recruiter and resume strategist specialized in {tier} roles. 
Analyze each project entry below and provide a comprehensive assessment.

For each project entry, your response must include:
1. "score": A score from 0-15 based on {tier} standards.
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
- 0-7 (POOR): Tutorial-level projects (e.g., Todo app, basic blog), CRUD without complexity, or ZERO metrics.
- 8-11 (AVERAGE): Solid personal projects with a complete tech stack but limited real-world usage or scale.
- 12-13 (STRONG): Technically complex projects (e.g., custom compilers, distributed systems) with real users or clear performance metrics.
- 14-15 (EXPERT): Production-grade applications, major open-source contributions, or projects solving highly advanced problems (e.g., 90% optimization on a known bottleneck).

General Guidelines:
- BE HIGHLY CRITICAL. Penalize heavily if the project looks like a generic classroom assignment.
- Focus on technical complexity and individual contribution.
- If bullets lack metrics, provide concrete advice on WHAT metric would be relevant (e.g., "Add metrics like accuracy percentage, users served, or performance improvement").
- Never fabricate numbers. If you can't infer a realistic metric, simply state what type of metric the user should add (e.g., "Add accuracy or dataset size" instead of "[X]%").

IMPORTANT: Output MUST be a valid JSON object with a key "entries" which is a list of objects, one for each project entry.

Projects Data:
{projects_data}

Return the JSON analysis."""


STANDARD_GUIDANCE = """Focus on:
- Technical Breadth: Show familiarity with common frameworks and libraries.
- Problem-Solving: Clearly state what problem the project solved.
- Tech Stack: Mention the primary tools and languages used.
- Outcomes: What was the result? (e.g., 'achieved 90% accuracy', 'deployed to AWS')."""

BIG_TECH_GUIDANCE = """Focus on domain-relevant projects with measurable impact. Adapt evaluation based on the candidate's field:

TECHNOLOGY & ENGINEERING:
- Architectural Complexity: Highlight use of distributed systems, cloud-native patterns, or complex APIs.
- Scale & Performance: Mention handling concurrent users, large datasets, or optimizing for low latency.
- Infrastructure: Show experience with CI/CD, monitoring, or containerization (Docker/Kubernetes).
- Engineering Best Practices: Mention unit testing, documentation, or code modularity.

FINANCE & BANKING:
- Deal Models: Highlight financial models built (DCF, LBO, merger models).
- Quantitative Analysis: Mention statistical models, risk simulations, or pricing engines.
- Tool Development: Show automation of trading, reporting, or compliance processes.
- Data Processing: Mention handling large financial datasets or real-time market data.

CONSULTING:
- Case Studies: Highlight problem-solving for Fortune 500 or major clients.
- Frameworks Applied: Reference strategic frameworks or analytical approaches.
- Client Impact: Show measurable outcomes (cost savings, revenue growth, efficiency).
- Deliverables: Mention presentations, dashboards, or strategic documents created.

PRODUCT MANAGEMENT:
- Product Features: Describe key features shipped and user adoption.
- Metrics Impact: Connect to KPIs like engagement, retention, or conversion.
- Research & Validation: Show user research, A/B testing, or feedback incorporation.
- Roadmap Planning: Highlight prioritization and feature roadmapping.

MARKETING & GROWTH:
- Campaign Projects: Describe marketing campaigns designed and executed.
- Channel Expertise: Highlight specific digital marketing channels.
- Content Creation: Show blogs, videos, or social media campaigns.
- Growth Experiments: Mention A/B tests, SEO improvements, or viral features.

DATA SCIENCE & ML:
- ML Models: Describe models built (classification, regression, NLP, computer vision).
- Model Performance: Quantify accuracy, precision, recall, or business impact.
- Data Pipeline: Show end-to-end ML pipelines or data engineering.
- Deployment: Mention MLOps, model serving, or production ML systems.

SALES & BUSINESS DEVELOPMENT:
- Deal Pipeline: Highlight deals sourced or closed through proactive efforts.
- Client Relationships: Show long-term relationships or strategic partnerships.
- Revenue Impact: Connect projects to revenue generation or growth.
- Territory Development: Mention new markets entered or segments penetrated.

OPERATIONS & SUPPLY CHAIN:
- Process Automation: Highlight automation of manual processes.
- Optimization Projects: Show cost savings, efficiency gains, or time reductions.
- System Implementation: Mention ERP, CRM, or workflow implementations.
- Vendor/Partner Projects: Show supplier negotiations or partner integrations.

Quantify outcomes with percentages, dollar amounts, or time saved wherever possible."""

STARTUP_GUIDANCE = """Focus on end-to-end ownership and measurable business impact. Adapt evaluation based on domain:

TECHNOLOGY & ENGINEERING:
- Product Ownership: Show how you took a project from idea to deployment.
- Speed & Iteration: Highlight rapid delivery of features or MVP development.
- Business Value: How did this project help users or the business?
- Full-stack Versatility: Show competence across the entire stack (Frontend, Backend, DB).
- Impact: Users launched to, revenue generated, time saved.

FINANCE & STARTUPS:
- Financial Tools: Built models, dashboards, or analytical tools quickly.
- Automation: Automated reporting, reconciliation, or financial processes.
- Fundraising: Created pitch decks, financial models, or investor materials.
- Quick Results: Delivered financial insights or tools fast with minimal resources.
- Adaptability: Built various tools as needs changed rapidly.

CONSULTING & PROFESSIONAL SERVICES:
- Client Deliverables: Analysis, presentations, or strategic documents created.
- Framework Application: Used or adapted strategic frameworks for clients.
- Rapid Delivery: Delivered quality work under tight deadlines.
- Problem-Solving: Solved ambiguous client problems creatively.
- Multiple Projects: Managed several client engagements simultaneously.

PRODUCT MANAGEMENT:
- Feature Shipped: Built and launched product features end-to-end.
- User Feedback Loop: Used user input to iterate and improve quickly.
- Cross-functional: Worked with design, engineering, marketing simultaneously.
- Metrics: Connected features to KPIs (engagement, retention, conversion).
- Ownership: Took full responsibility from idea to launch.

MARKETING & GROWTH:
- Campaign Projects: Designed and executed marketing campaigns.
- Content Creation: Built blogs, videos, social media assets.
- Growth Experiments: Ran A/B tests, SEO improvements, email campaigns.
- Tools Built: Landing pages, email sequences, automation workflows.
- Quick Wins: Achieved measurable results fast with minimal budget.

DATA SCIENCE & ML:
- End-to-End ML: Built models from data to deployment quickly.
- Prototyping: Created quick ML demos or proofs of concept.
- Business Application: Connected ML to real business problems.
- Rapid Iteration: Improved models based on feedback fast.
- Tool Building: Created internal tools for data or ML workflows.

SALES & BUSINESS DEVELOPMENT:
- Pipeline Tools: Built CRM workflows, outreach sequences.
- Client Demos: Created product demonstrations or sales materials.
- Relationship Tools: Built tracking systems for client relationships.
- Quick Proposals: Created proposals or pitch materials fast.
- Revenue Projects: Directly contributed to deals or revenue.

OPERATIONS & ADMIN:
- Process Automation: Automated manual workflows or processes.
- Tool Implementation: Set up tools like Notion, Airtable, Zapier quickly.
- System Building: Created operational systems from scratch.
- Cost Savings: Reduced costs through efficient solutions.
- Quick Scaling: Built infrastructure to handle growth fast.

Quantify outcomes with numbers. Show ownership, speed, and business impact."""

QUANT_GUIDANCE = """Focus on:
- Technical Depth: Highlight low-level language features (C++ templates, Rust lifetimes) or memory optimization.
- Algorithm Performance: Quantify the speed-up or complexity reduction achieved.
- Mathematical Rigor: Mention specific algorithms, statistical methods, or quantitative models used.
- Precision: Show extreme attention to detail and correctness in implementation."""

TIER_TEMPLATES = {
    "STANDARD": BASE_PROJECTS_PROMPT.format(tier="STANDARD", tier_specific_guidance=STANDARD_GUIDANCE, projects_data="{projects_data}"),
    "BIG_TECH": BASE_PROJECTS_PROMPT.format(tier="BIG TECH FANG", tier_specific_guidance=BIG_TECH_GUIDANCE, projects_data="{projects_data}"),
    "STARTUP": BASE_PROJECTS_PROMPT.format(tier="STARTUP", tier_specific_guidance=STARTUP_GUIDANCE, projects_data="{projects_data}"),
    "QUANT": BASE_PROJECTS_PROMPT.format(tier="QUANT", tier_specific_guidance=QUANT_GUIDANCE, projects_data="{projects_data}"),
}


def get_projects_prompt(tier: str) -> ChatPromptTemplate:
    """Get the projects analysis prompt for a specific tier."""
    tier_context = tier.upper().replace(" ", "_")
    
    # Fallback to standard if tier not found
    template = TIER_TEMPLATES.get(tier_context, TIER_TEMPLATES["STANDARD"])
    
    return ChatPromptTemplate.from_template(template)


def format_projects_data(project_entries):
    """Format project entries for the LLM prompt."""
    proj_data = []
    for i, proj in enumerate(project_entries):
        proj_data.append({
            "entry_index": i,
            "name": proj.name,
            "bullets": {idx: bullet for idx, bullet in enumerate(proj.descriptions or [])},
        })
    import json
    return json.dumps(proj_data, indent=2)
