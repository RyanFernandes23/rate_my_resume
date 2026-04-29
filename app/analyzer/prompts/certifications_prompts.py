"""Certifications analyzer prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate


BASE_CERTIFICATIONS_PROMPT = """You are a senior recruiter specialized in {tier} roles. Analyze the certifications section below with {tier} expectations in mind.

Recruiter Perspective for {tier}:
{tier_specific_guidance}

Analyze each certification entry:
1. Check if organization/issuer name is valid and respected in {tier} roles.
2. Validate dates if provided.
3. Check if link is provided and valid format.
4. Determine if certification is relevant to the {tier} career path.

For each certification, return a JSON object with:
{{{{
    "index": 0,
    "name": "Certification Name",
    "is_valid": true/false,
    "organization_issues": ["issue1", "issue2"],
    "date_issues": ["issue1", "issue2"],
    "link_issues": ["issue1", "issue2"],
    "suggestions": ["Specific feedback about this certification (e.g., 'This AWS cert is valuable for {tier} roles. Consider adding a cloud-focused specialty like Solutions Architect Associate to strengthen your profile.')"]
}}}}

Certifications Data:
{certifications_data}

Return a JSON array of analysis objects for each certification."""

STANDARD_GUIDANCE = """- Value recognized industry certifications (e.g., CompTIA, Microsoft, Oracle).
- Certifications should show continuous learning and professional growth."""

BIG_TECH_GUIDANCE = """Evaluate certifications based on the candidate's domain:

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

STARTUP_GUIDANCE = """Evaluate certifications based on practical, high-impact skills for startups. Adapt based on domain:

TECHNOLOGY & ENGINEERING:
- Value specialized, high-productivity certifications (e.g., dbt, specific cloud tool mastery).
- Certifications showing full-stack or DevOps versatility are preferred.
- Look for: AWS/GCP/Azure quick certs, Vercel, Supabase, or modern tool certifications.
- Prioritize: Skills that enable shipping fast with minimal resources.

FINANCE & STARTUPS:
- Value quick, practical finance certifications over lengthy programs.
- Look for: Bloomberg Market Concepts, financial modeling quick courses, fintech certifications.
- Prioritize: Skills in startup finance, fundraising, or financial planning.
- Less emphasis on traditional CFA/CPA unless specifically needed.

CONSULTING & PROFESSIONAL SERVICES:
- Value certifications showing rapid skill acquisition.
- Look for: Short courses in relevant domains, agile certifications, workshop facilitator certs.
- Prioritize: Skills in communication, project management, or specific methodologies.
- Value: Quick learners with versatile skill sets.

PRODUCT MANAGEMENT:
- Value product-focused certifications showing end-to-end ownership.
- Look for: Product School, Pragmatic Institute, or similar practical certs.
- Prioritize: Skills in user research, analytics, or product strategy.
- Value: Hands-on product experience over theory.

MARKETING & GROWTH:
- Value certifications showing measurable skills.
- Look for: Google Ads, HubSpot, Facebook Blueprint, or similar platform certs.
- Prioritize: Skills in growth, content, or digital marketing.
- Value: Results-oriented certifications with clear metrics.

DATA SCIENCE & ML:
- Value quick, practical ML certifications.
- Look for: Coursera, fast.ai, or cloud ML certifications.
- Prioritize: Skills in end-to-end ML, deployment, or business application.
- Value: Practical ML over theoretical depth.

SALES & BUSINESS DEVELOPMENT:
- Value CRM and sales methodology certifications.
- Look for: HubSpot Sales Pro, Salesforce admin, or similar quick certs.
- Prioritize: Skills in pipeline, negotiation, or client relationships.
- Value: Certifications showing direct revenue impact.

OPERATIONS & ADMIN:
- Value process and productivity certifications.
- Look for: Agile, Scrum, or no-code tool certifications.
- Prioritize: Skills in automation, process improvement, or scaling.
- Value: Certifications showing resourcefulness.

Focus on certifications that demonstrate ability to deliver quick value in startup environments."""

QUANT_GUIDANCE = """- Certifications are less common; prioritize those in high-performance computing or specialized finance.
- Value deep technical certifications from hardware or low-level systems vendors."""

TIER_TEMPLATES = {
    "STANDARD": BASE_CERTIFICATIONS_PROMPT.format(tier="STANDARD", tier_specific_guidance=STANDARD_GUIDANCE, certifications_data="{certifications_data}"),
    "BIG_TECH": BASE_CERTIFICATIONS_PROMPT.format(tier="BIG TECH FANG", tier_specific_guidance=BIG_TECH_GUIDANCE, certifications_data="{certifications_data}"),
    "STARTUP": BASE_CERTIFICATIONS_PROMPT.format(tier="STARTUP", tier_specific_guidance=STARTUP_GUIDANCE, certifications_data="{certifications_data}"),
    "QUANT": BASE_CERTIFICATIONS_PROMPT.format(tier="QUANT", tier_specific_guidance=QUANT_GUIDANCE, certifications_data="{certifications_data}"),
}


def get_certifications_prompt(tier: str = "STANDARD") -> ChatPromptTemplate:
    """Get the certifications analysis prompt for a specific tier."""
    tier_context = tier.upper().replace(" ", "_")
    template = TIER_TEMPLATES.get(tier_context, TIER_TEMPLATES["STANDARD"])
    return ChatPromptTemplate.from_template(template)


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
