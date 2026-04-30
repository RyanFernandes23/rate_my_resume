"""Skills analyzer prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate

ENTERPRISE_GUIDANCE = """Focus on a diverse set of skills based on the candidate's domain with professional enterprise standards. Adapt evaluation based on the field:

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

BASE_SKILLS_PROMPT = """You are a resume analysis expert specializing in professional enterprise technical recruiting.

Analyze the skills section for professional enterprise alignment:
Focus on a diverse set of skills based on the candidate's domain with professional enterprise standards. Adapt evaluation based on the field:

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

Select the most relevant skill categories based on the candidate's actual experience and the target role. Prioritize skills that demonstrate impact, scalability, and business value regardless of domain.

SCORING_RUBRIC (STRICT):
- 0-7 (POOR): Lacks core technologies for professional enterprise roles. Many listed skills have NO evidence in Experience/Projects.
- 8-11 (AVERAGE): Good breadth of skills, but some mismatch with enterprise standards or missing evidence for 50%+ of the list.
- 12-13 (STRONG): Highly relevant stack for professional enterprise roles with clear evidence of application in most entries.
- 14-15 (EXPERT): Mastery of advanced/niche enterprise technologies with deep evidence across multiple high-impact experiences.

STRICTNESS RULES:
- BE CRITICAL. If a skill is listed but NEVER mentioned in experience bullets, penalize heavily.
- Penalize "soft skills" (e.g., "Team Player") if they take up space in a technical resume.
- Check if the "Powerhouse" languages and tools for the domain are present.

Return a JSON object with:
{{
    "score": A score from 0-15 based on professional enterprise standards.,
    "reasoning": "A brief explanation of why this score was given based on professional enterprise expectations.",
    "total_count": number,
    "skills_list": ["skill1", "skill2"],
    "listed_in_exp_projects": ["skill1", "skill2"],
    "missing_from_skills": ["skill1", "skill2"],
    "redundant_skills": ["skill1", "skill2"],
    "issues": [{{ "issue": "description", "severity": "high/medium/low", "reason": "explanation" }}],
    "suggestions": ["Direct, conversational feedback (e.g., 'I noticed you have strong Backend skills but no mention of Cloud platforms. For professional enterprise roles, adding AWS or Docker would significantly strengthen your profile.')"]
}}

Resume Skills:
{{skills_list}}

Experience Descriptions:
{{exp_descriptions}}

Project Descriptions:
{{proj_descriptions}}

Return a JSON object with the analysis."""


def get_skills_prompt(tier: str = None) -> ChatPromptTemplate:
    """Get the skills analysis prompt."""
    return ChatPromptTemplate.from_template(BASE_SKILLS_PROMPT)


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
