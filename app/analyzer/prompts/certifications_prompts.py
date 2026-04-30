"""Certifications analyzer prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate

ENTERPRISE_GUIDANCE = """Evaluate certifications based on the candidate's domain with professional enterprise standards:

TECHNOLOGY & ENGINEERING:
- High value on cloud provider certifications (AWS Solutions Architect, Google Professional Cloud Architect, Azure Administrator).
- Value security certifications (CISSP, CISM, CompTIA Security+).
- Look for Kubernetes (CKAD, CKA), DevOps (AWS DevOps Engineer, GCP Cloud Run), or specialized vendor-neutral certifications.
- Also value: PMP, ITIL for operations roles.

FINANCE & BANKING:
- High value on CFA (Chartered Financial Analyst), FRM (Financial Risk Manager), CPA (Certified Public Accountant).
- Look for certifications in financial modeling, Bloomberg, or trading platforms.
- Value regulatory certifications (Series 7, Series 66 for US; relevant local licenses).
- Also value: MBA, specialized finance certifications.

CONSULTING:
- Value case methodology certifications or internal firm training.
- Look for project management (PMP, PRINCE2) or process improvement (Lean Six Sigma).
- Business analysis certifications (CBAP, CCBA) are valued.
- Also value: Strategy or management certifications.

PRODUCT MANAGEMENT:
- Value product management certifications (Product School, Pragmatic Institute).
- Look for analytics certifications (Google Analytics, Mixpanel, Amplitude).
- Scrum/Agile certifications (PSM, CSPO) are valued.
- Also value: Design thinking or UX certifications.

MARKETING & GROWTH:
- High value on Google Ads, Facebook Blueprint, or HubSpot certifications.
- Look for analytics certifications (Google Analytics, Adobe Analytics).
- SEO/SEM certifications (Moz, Ahrefs) are valued.
- Also value: Content marketing, social media, or email marketing certifications.

DATA SCIENCE & ML:
- Value cloud ML certifications (AWS Machine Learning, Google Cloud ML, Azure AI).
- Look for ML/DL courses certificates (Coursera, fast.ai, deeplearning.ai).
- Data engineering certifications (Snowflake, Databricks, dbt) are valued.
- Also value: TensorFlow, PyTorch, or specialized ML certifications.

SALES & BUSINESS DEVELOPMENT:
- Value CRM certifications (Salesforce Administrator, HubSpot Sales Pro).
- Look for negotiation or strategic selling certifications.
- Sales methodology certifications (Sandler, Challenger, SPIN) are valued.
- Also value: LinkedIn Sales Navigator, cold outreach tools.

OPERATIONS & SUPPLY CHAIN:
- High value on Lean Six Sigma (Green Belt, Black Belt).
- Look for APICS/ASC (CPIM, CSCP) certifications for supply chain.
- ERP certifications (SAP, Oracle) are valued.
- Also value: Project management (PMP) or operations management.

Prioritize certifications that demonstrate current, relevant skills in the candidate's target field."""

BASE_CERTIFICATIONS_PROMPT = """You are a senior recruiter specialized in professional enterprise roles. Analyze the certifications section below with production-grade enterprise expectations in mind.

Recruiter Perspective:
Evaluate certifications based on the candidate's domain with professional enterprise standards:

TECHNOLOGY & ENGINEERING:
- High value on cloud provider certifications (AWS Solutions Architect, Google Professional Cloud Architect, Azure Administrator).
- Value security certifications (CISSP, CISM, CompTIA Security+).
- Look for Kubernetes (CKAD, CKA), DevOps (AWS DevOps Engineer, GCP Cloud Run), or specialized vendor-neutral certifications.
- Also value: PMP, ITIL for operations roles.

FINANCE & BANKING:
- High value on CFA (Chartered Financial Analyst), FRM (Financial Risk Manager), CPA (Certified Public Accountant).
- Look for certifications in financial modeling, Bloomberg, or trading platforms.
- Value regulatory certifications (Series 7, Series 66 for US; relevant local licenses).
- Also value: MBA, specialized finance certifications.

CONSULTING:
- Value case methodology certifications or internal firm training.
- Look for project management (PMP, PRINCE2) or process improvement (Lean Six Sigma).
- Business analysis certifications (CBAP, CCBA) are valued.
- Also value: Strategy or management certifications.

PRODUCT MANAGEMENT:
- Value product management certifications (Product School, Pragmatic Institute).
- Look for analytics certifications (Google Analytics, Mixpanel, Amplitude).
- Scrum/Agile certifications (PSM, CSPO) are valued.
- Also value: Design thinking or UX certifications.

MARKETING & GROWTH:
- High value on Google Ads, Facebook Blueprint, or HubSpot certifications.
- Look for analytics certifications (Google Analytics, Adobe Analytics).
- SEO/SEM certifications (Moz, Ahrefs) are valued.
- Also value: Content marketing, social media, or email marketing certifications.

DATA SCIENCE & ML:
- Value cloud ML certifications (AWS Machine Learning, Google Cloud ML, Azure AI).
- Look for ML/DL courses certificates (Coursera, fast.ai, deeplearning.ai).
- Data engineering certifications (Snowflake, Databricks, dbt) are valued.
- Also value: TensorFlow, PyTorch, or specialized ML certifications.

SALES & BUSINESS DEVELOPMENT:
- Value CRM certifications (Salesforce Administrator, HubSpot Sales Pro).
- Look for negotiation or strategic selling certifications.
- Sales methodology certifications (Sandler, Challenger, SPIN) are valued.
- Also value: LinkedIn Sales Navigator, cold outreach tools.

OPERATIONS & SUPPLY CHAIN:
- High value on Lean Six Sigma (Green Belt, Black Belt).
- Look for APICS/ASC (CPIM, CSCP) certifications for supply chain.
- ERP certifications (SAP, Oracle) are valued.
- Also value: Project management (PMP) or operations management.

Prioritize certifications that demonstrate current, relevant skills in the candidate's target field.

Analyze each certification entry:
1. Check if organization/issuer name is valid and respected in professional enterprise roles.
2. Validate dates if provided.
3. Check if link is provided and valid format.
4. Determine if certification is relevant to a professional enterprise career path.

For each certification, return a JSON object with:
{{
    "index": 0,
    "name": "Certification Name",
    "is_valid": true/false,
    "organization_issues": ["issue1", "issue2"],
    "date_issues": ["issue1", "issue2"],
    "link_issues": ["issue1", "issue2"],
    "suggestions": ["Specific feedback about this certification (e.g., 'This AWS cert is valuable for enterprise roles. Consider adding a cloud-focused specialty like Solutions Architect Associate to strengthen your profile.')"]
}}

Certifications Data:
{{certifications_data}}

Return a JSON array of analysis objects for each certification."""


def get_certifications_prompt(tier: str = None) -> ChatPromptTemplate:
    """Get the certifications analysis prompt."""
    return ChatPromptTemplate.from_template(BASE_CERTIFICATIONS_PROMPT)


def format_certifications_data(certifications):
    """Format certification entries for the LLM prompt."""
    cert_data = []
    for i, cert in enumerate(certifications):
        cert_data.append({
            "index": i,
            "name": cert.name,
            "issuer": cert.issuer,
            "date": cert.date,
            "link": cert.link,
        })
    import json
    return json.dumps(cert_data, indent=2)
