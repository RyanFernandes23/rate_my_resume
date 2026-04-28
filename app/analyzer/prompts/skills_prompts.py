"""Skills analyzer prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate


BASE_SKILLS_PROMPT = """You are a resume analysis expert specializing in {tier} technical recruiting.

Analyze the skills section for {tier} alignment:
{tier_specific_guidance}

SCORING_RUBRIC (STRICT):
- 0-7 (POOR): Lacks core technologies for {tier}. Many listed skills have NO evidence in Experience/Projects.
- 8-11 (AVERAGE): Good breadth of skills, but some mismatch with {tier} or missing evidence for 50%+ of the list.
- 12-13 (STRONG): Highly relevant stack for {tier} with clear evidence of application in most entries.
- 14-15 (EXPERT): Mastery of advanced/niche {tier} technologies with deep evidence across multiple high-impact experiences.

STRICTNESS RULES:
- BE CRITICAL. If a skill is listed but NEVER mentioned in experience bullets, penalize heavily.
- Penalize "soft skills" (e.g., "Team Player") if they take up space in a technical resume.
- For {tier}, check if the "Powerhouse" languages and tools are present.

Return a JSON object with:
{{{{
    "score": A score from 0-15 based on {tier} standards.,
    "reasoning": "A brief explanation of why this score was given based on {tier} expectations.",
    "total_count": number,
    "skills_list": ["skill1", "skill2"],
    "listed_in_exp_projects": ["skill1", "skill2"],
    "missing_from_skills": ["skill1", "skill2"],
    "redundant_skills": ["skill1", "skill2"],
    "issues": [{{{{ "issue": "description", "severity": "high/medium/low", "reason": "explanation" }}}}],
    "suggestions": ["Direct, conversational feedback (e.g., 'I noticed you have strong Backend skills but no mention of Cloud platforms. For {tier}, adding AWS or Docker would significantly strengthen your profile.')"]
}}}}

Resume Skills:
{skills_list}

Experience Descriptions:
{exp_descriptions}

Project Descriptions:
{proj_descriptions}

Return a JSON object with the analysis."""


STANDARD_GUIDANCE = """Focus on:
- Breadth of Industry Standards: Ensure familiarity with popular languages and frameworks.
- Categorization: Skills should be logically grouped (Languages, Frameworks, Tools, Databases, soft skills, etc).
- Evidence: Most skills listed should appear in the Experience or Projects sections.
- Relevance: Prioritize skills currently in high demand for general roles."""

BIG_TECH_GUIDANCE = """Focus on a diverse set of skills based on the candidate's domain. Adapt evaluation based on the field:

TECHNOLOGY & ENGINEERING:
- Infrastructure & Scale: Prioritize Kubernetes, Docker, Terraform, and cloud platforms (AWS, GCP, Azure).
- System Architecture: Highlight distributed systems, microservices, and message queues.
- Backend Powerhouses: Deep knowledge of languages (Python, Go, Java, Rust) and frameworks is valued.
- Monitoring & Reliability: Mention tools like Prometheus, Grafana, or Datadog.

FINANCE & BANKING:
- Financial Modeling: Excel, VBA, Python (pandas, NumPy), R.
- Trading Systems: Bloomberg Terminal, FactSet, Refinitiv, SQL.
- Risk Management: VaR, Monte Carlo simulations, credit risk models.
- Regulatory Knowledge: Basel III, SOX, GDPR compliance.

CONSULTING:
- Strategic Frameworks: BCG, McKinsey, Bain case frameworks.
- Data Analysis: Excel advanced, Tableau, Power BI, SQL.
- Project Management: Agile, Scrum, JIRA, Asana.
- Client Communication: Presentation tools, stakeholder management.

PRODUCT MANAGEMENT:
- Product Tools: Figma, Sketch, Miro, Productboard.
- Analytics: Mixpanel, Amplitude, Google Analytics, SQL.
- Agile/Scrum: JIRA, Confluence, roadmapping tools.
- User Research: Surveys, user interviews, A/B testing.

MARKETING & GROWTH:
- Digital Marketing: SEO, SEM, Google Ads, Facebook Ads Manager.
- Analytics: Google Analytics, Adobe Analytics, SQL.
- Content & Design: Photoshop, Canva, HubSpot, Mailchimp.
- Social Media: LinkedIn, Twitter analytics, community management.

DATA SCIENCE & ML:
- Languages: Python, R, SQL, Scala.
- ML/AI: TensorFlow, PyTorch, scikit-learn, Hugging Face.
- Data Engineering: Spark, Airflow, dbt, Snowflake.
- MLOps: Kubeflow, MLflow, Kubernetes for ML.

SALES & BUSINESS DEVELOPMENT:
- CRM: Salesforce, HubSpot, Pipedrive.
- Sales Tools: LinkedIn Sales Navigator, ZoomInfo, Apollo.
- Analytics: Excel, Tableau, SQL for pipeline analysis.
- Negotiation: Value selling, consultative selling, strategic partnerships.

OPERATIONS & SUPPLY CHAIN:
- ERP Systems: SAP, Oracle, NetSuite.
- Process Improvement: Lean Six Sigma, process mapping.
- Logistics: SAP TM, Oracle TMS, warehouse management.
- Data Analysis: Excel, Power BI, SQL for optimization.

Select the most relevant skill categories based on the candidate's actual experience and the target role. Prioritize skills that demonstrate impact, scalability, and business value regardless of domain."""

STARTUP_GUIDANCE = """Focus on versatile, high-impact skills across domains. Adapt evaluation based on the candidate's field:

TECHNOLOGY & ENGINEERING:
- Full-Stack Versatility: Prioritize skills that show the ability to work across the entire stack (Next.js, TypeScript, PostgreSQL, Prisma).
- Modern Web Technologies: Focus on high-productivity tools like Tailwind CSS, Supabase, or Vercel.
- Deployment & CI/CD: Show familiarity with Vercel, Netlify, GitHub Actions, or Railway.
- Product-Mindset: Mention skills related to analytics or A/B testing (Mixpanel, PostHog, Amplitude).
- Rapid Prototyping: Highlight skills in fast iteration, MVP development, and iterating based on feedback.

FINANCE & STARTUPS:
- Financial Modeling: Excel, Google Sheets, Python (pandas), SQL for startup metrics.
- Fundraising: Understand pitch decks, unit economics, CAC, LTV, runway.
- Growth Metrics: MRR, ARR, churn, cohort analysis.
- Tooling: QuickBooks, Stripe, AngelList, PitchBook.
- Adaptability: Show ability to wear multiple hats in fast-changing environments.

CONSULTING & PROFESSIONAL SERVICES:
- Client-Facing Skills: Presentation tools, stakeholder communication, workshop facilitation.
- Rapid Learning: Ability to quickly understand new industries and domains.
- Frameworks: Agile, Design Thinking, Lean Startup methodologies.
- Tools: Miro, Figma, Notion, Asana for collaborative work.
- Business Acumen: Basic financial modeling, competitive analysis, market sizing.

PRODUCT MANAGEMENT:
- Product Tools: Figma, Sketch, Miro, Productboard, Linear.
- Analytics: Mixpanel, Amplitude, PostHog, Google Analytics.
- Agile/Scrum: JIRA, Confluence, notion, roadmapping tools.
- User Research: Surveys, user interviews, feedback loops, A/B testing.
- Technical Fluency: Understanding of APIs, databases, and basic development.

MARKETING & GROWTH:
- Digital Marketing: SEO, SEM, Google Ads, Facebook Ads, LinkedIn Ads.
- Growth Tools: HubSpot, Mailchimp, ConvertKit, Buffer.
- Analytics: Google Analytics, Amplitude, Mixpanel, SQL.
- Content: WordPress, Webflow, Canva, Figma for quick designs.
- Social: Community management, viral loops, referral programs.

DATA SCIENCE & ML:
- End-to-End: Python, SQL, Jupyter, cloud platforms (AWS/GCP).
- Rapid Prototyping: Streamlit, Gradio, FastAPI for quick ML demos.
- MLOps Lite: GitHub Actions, Docker, basic deployment.
- Experimentation: A/B testing, statistical significance, analytics.
- Open Source: Hugging Face, Kaggle, collaboration tools.

SALES & BUSINESS DEVELOPMENT:
- CRM: HubSpot, Pipedrive, Salesforce (lightweight versions).
- Outreach Tools: Apollo, LinkedIn Sales Navigator, ZeroBounce.
- Communication: Cold email, cold calling, demo skills.
- Pipeline Management: Excel/Sheets, basic SQL for tracking.
- Entrepreneurial: Hunting new business, building relationships fast.

OPERATIONS & ADMIN:
- Productivity Tools: Notion, Asana, ClickUp, Airtable.
- No-Code: Zapier, Make, Bubble for automation.
- Basic Finance: QuickBooks, Expensify, Stripe reconciliation.
- Communication: Slack, Discord, Zoom for remote teams.
- Adaptability: Multi-tasking, quick pivots, resourcefulness.

Prioritize skills that show versatility, rapid learning, and ability to deliver impact with limited resources."""

QUANT_GUIDANCE = """Focus on:
- Performance Engineering: Prioritize C++ (modern standards), Rust, and assembly-level optimization.
- Hardware/System Knowledge: Highlight memory management, multi-threading, and kernel optimization skills.
- Mathematical Foundation: Mention skills in statistics, probability, or numerical methods.
- Specialized Tools: Focus on high-performance libraries like NumPy, PyTorch (low-level), or specialized database systems (KDB+)."""

TIER_TEMPLATES = {
    "STANDARD": BASE_SKILLS_PROMPT.format(tier="STANDARD", tier_specific_guidance=STANDARD_GUIDANCE, skills_list="{skills_list}", exp_descriptions="{exp_descriptions}", proj_descriptions="{proj_descriptions}"),
    "BIG_TECH": BASE_SKILLS_PROMPT.format(tier="BIG TECH FANG", tier_specific_guidance=BIG_TECH_GUIDANCE, skills_list="{skills_list}", exp_descriptions="{exp_descriptions}", proj_descriptions="{proj_descriptions}"),
    "STARTUP": BASE_SKILLS_PROMPT.format(tier="STARTUP", tier_specific_guidance=STARTUP_GUIDANCE, skills_list="{skills_list}", exp_descriptions="{exp_descriptions}", proj_descriptions="{proj_descriptions}"),
    "QUANT": BASE_SKILLS_PROMPT.format(tier="QUANT", tier_specific_guidance=QUANT_GUIDANCE, skills_list="{skills_list}", exp_descriptions="{exp_descriptions}", proj_descriptions="{proj_descriptions}"),
}


def get_skills_prompt(tier: str) -> ChatPromptTemplate:
    """Get the skills analysis prompt for a specific tier."""
    tier_context = tier.upper().replace(" ", "_")
    
    # Fallback to standard if tier not found
    template = TIER_TEMPLATES.get(tier_context, TIER_TEMPLATES["STANDARD"])
    
    return ChatPromptTemplate.from_template(template)


def format_skills_data(skills_list, experience_entries, project_entries):
    """Format skills data for the LLM prompt."""
    import json
    exp_descriptions = [desc for exp in (experience_entries or []) for desc in (exp.descriptions or [])]
    proj_descriptions = [desc for proj in (project_entries or []) for desc in (proj.descriptions or [])]
    return {
        "skills_list": json.dumps(skills_list or [], indent=2),
        "exp_descriptions": json.dumps(exp_descriptions, indent=2),
        "proj_descriptions": json.dumps(proj_descriptions, indent=2),
    }
