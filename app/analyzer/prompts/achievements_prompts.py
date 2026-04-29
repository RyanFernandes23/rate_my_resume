"""Achievements and hobbies analyzer prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate


BASE_ACHIEVEMENTS_PROMPT = """You are a senior recruiter specialized in {tier} roles. Analyze the achievements and hobbies section below with {tier} expectations in mind.

Recruiter Perspective for {tier}:
{tier_specific_guidance}

Analyze achievements:
1. Evaluate impact of each achievement based on {tier} standards.
2. Determine if it should be kept or removed.
3. Check for typos, grammar issues.
4. Verify relevance to {tier} career path.

Analyze hobbies:
1. Determine if hobby adds character or shows relevant traits (e.g., leadership, discipline, technical curiosity).
2. Consider removing very common/unprofessional hobbies.

For achievements, return array:
[
  {{{{
    "index": 0,
    "title": "Achievement title",
    "impact_score": number (0-10),
    "recommendation": "keep/remove",
    "reasoning": "explanation why keep or remove",
    "issues": ["issue1", "issue2"]
  }}}}
]

For hobbies, return array:
[
  {{{{
    "hobby": "hobby name",
    "is_professional": true/false,
    "suggestions": ["suggestion if needed"]
  }}}}
]

Return a JSON object with:
{{{{
    "achievements": [...],
    "hobbies": [...],
    "suggestions": ["Specific feedback about achievements and hobbies (e.g., 'Your competitive programming experience is a strong signal for {tier} roles. Highlighting your Codeforces rank prominently would help you stand out.')"],
    "score": number (out of 10)
}}}}

Achievements:
{achievements_data}

Hobbies/Extra-curricular:
{hobbies_data}

Return a JSON object with the analysis."""

STANDARD_GUIDANCE = """- Look for professional recognition and certifications.
- Value standard career-related awards and community involvement.
- Hobbies should show a well-rounded personality."""

BIG_TECH_GUIDANCE = """Evaluate achievements based on the candidate's domain:

TECHNOLOGY & ENGINEERING:
- High value on Open-source contributions and Technical certifications.
- Value hackathon wins and internal recognition in large companies.
- Look for AWS, GCP, Azure, Kubernetes, or cloud certifications.
- Hobbies showing technical curiosity (e.g., Home Lab, Game Dev, open source) are a plus.

FINANCE & BANKING:
- High value on CFA, FRM, CPA, or other finance certifications.
- Look for trading competitions, stock pitch contests, or finance club leadership.
- Value relevant coursework certifications or Bloomberg Terminal proficiency.
- Hobbies showing intellectual rigor (reading, research, analytical games) add value.

CONSULTING:
- High value on case competition wins (McKinsey, BCG, Bain cups).
- Look for student consulting clubs, entrepreneurship centers, or business competitions.
- Leadership in clubs, organizations, or community service shows well-roundedness.
- Hobbies showing strategic thinking or leadership (team sports, debating) are valued.

PRODUCT MANAGEMENT:
- Value product hackathons, design challenges, or user research projects.
- Look for leadership in student organizations or product-focused clubs.
- Entrepreneurship (side projects, startups) shows initiative.
- Hobbies showing user-centric thinking (design, photography, user research) are relevant.

MARKETING & GROWTH:
- Value marketing competitions, ad campaigns managed, or social media growth.
- Look for certifications in Google Ads, HubSpot, or social media tools.
- Content creation (blogs, YouTube, podcasts) demonstrates skills.
- Hobbies showing creativity (writing, design, video production) align well.

DATA SCIENCE & ML:
- High value on Kaggle competitions, hackathon wins, or research papers.
- Look for competitive programming (Codeforces, LeetCode) or math competitions.
- Value certifications from Coursera, edX, or deep learning courses.
- Hobbies showing analytical thinking (puzzles, chess, data projects) are relevant.

SALES & BUSINESS DEVELOPMENT:
- Value sales competitions, business development challenges, or networking events.
- Look for leadership in clubs, entrepreneurship, or fundraising achievements.
- Sports or activities demonstrating persistence and goal orientation.
- Hobbies showing relationship-building or communication skills add value.

OPERATIONS & SUPPLY CHAIN:
- Value Lean Six Sigma certifications or process improvement projects.
- Look for operations challenges, supply chain competitions, or logistics projects.
- Leadership in clubs or community service shows well-roundedness.
- Hobbies showing analytical thinking or systematic approaches are valued.

Provide domain-appropriate evaluation of achievements and recommendations."""

STARTUP_GUIDANCE = """Evaluate achievements based on entrepreneurial mindset and versatility across domains:

TECHNOLOGY & ENGINEERING:
- Value 0-to-1 launches and entrepreneurial achievements.
- High value on hackathons and community leadership.
- Look for: Side projects, open source contributions, hackathon wins, coding competitions.
- Hobbies showing grit or high-energy (endurance sports, specialized technical projects).

FINANCE & STARTUPS:
- Value financial competitions, startup involvement, or side businesses.
- High value on fundraising, pitch competitions, or financial modeling contests.
- Look for: Finance clubs, investment societies, entrepreneurship centers.
- Hobbies showing financial acumen or business mindset.

CONSULTING & PROFESSIONAL SERVICES:
- Value case competition wins and leadership in clubs.
- High value on diverse experiences and rapid learning.
- Look for: Consulting clubs, case competitions, leadership roles.
- Hobbies showing communication or strategic thinking.

PRODUCT MANAGEMENT:
- Value product hackathons and user research projects.
- High value on launching side projects or products.
- Look for: Product clubs, user research, building apps/products.
- Hobbies showing user-centric thinking or creativity.

MARKETING & GROWTH:
- Value marketing competitions and content creation.
- High value on personal branding or social media presence.
- Look for: Marketing clubs, campaigns run, content created.
- Hobbies showing creativity, communication, or community building.

DATA SCIENCE & ML:
- Value hackathons, Kaggle competitions, or ML projects.
- High value on end-to-end projects or deployments.
- Look for: ML competitions, research, open source ML contributions.
- Hobbies showing analytical thinking or technical curiosity.

SALES & BUSINESS DEVELOPMENT:
- Value sales competitions, networking events, or business development.
- High value on entrepreneurial activities or side businesses.
- Look for: Sales clubs, fundraising, business competitions.
- Hobbies showing persistence, communication, or relationship building.

OPERATIONS & ADMIN:
- Value process improvement projects and leadership.
- High value on multi-tasking and resourcefulness.
- Look for: Operations clubs, leadership, practical problem-solving.
- Hobbies showing organizational skills or efficiency.

Focus on initiative, ownership, and demonstrated ability to deliver results quickly."""

QUANT_GUIDANCE = """- Extreme emphasis on Competitive Programming (Codeforces Rank, ICPC) and Mathematical Awards (IMO, Putnam).
- Value research papers and deep technical contributions.
- Hobbies should ideally show discipline or high cognitive load (e.g., Chess, Bridge)."""

TIER_TEMPLATES = {
    "STANDARD": BASE_ACHIEVEMENTS_PROMPT.format(tier="STANDARD", tier_specific_guidance=STANDARD_GUIDANCE, achievements_data="{achievements_data}", hobbies_data="{hobbies_data}"),
    "BIG_TECH": BASE_ACHIEVEMENTS_PROMPT.format(tier="BIG TECH FANG", tier_specific_guidance=BIG_TECH_GUIDANCE, achievements_data="{achievements_data}", hobbies_data="{hobbies_data}"),
    "STARTUP": BASE_ACHIEVEMENTS_PROMPT.format(tier="STARTUP", tier_specific_guidance=STARTUP_GUIDANCE, achievements_data="{achievements_data}", hobbies_data="{hobbies_data}"),
    "QUANT": BASE_ACHIEVEMENTS_PROMPT.format(tier="QUANT", tier_specific_guidance=QUANT_GUIDANCE, achievements_data="{achievements_data}", hobbies_data="{hobbies_data}"),
}


def get_achievements_prompt(tier: str = "STANDARD") -> ChatPromptTemplate:
    """Get the achievements analysis prompt for a specific tier."""
    tier_context = tier.upper().replace(" ", "_")
    template = TIER_TEMPLATES.get(tier_context, TIER_TEMPLATES["STANDARD"])
    return ChatPromptTemplate.from_template(template)


def format_achievements_data(achievements, hobbies, extra_curricular):
    """Format achievements and hobbies data for the LLM prompt."""
    import json
    return {
        "achievements_data": json.dumps([{"title": a.title, "descriptions": a.descriptions} for a in (achievements or [])], indent=2),
        "hobbies_data": json.dumps([h for h in (hobbies or []) + (extra_curricular or [])], indent=2),
    }
