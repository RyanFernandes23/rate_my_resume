"""Achievements analyzer prompt templates using LangChain."""
from langchain_core.prompts import ChatPromptTemplate

ENTERPRISE_GUIDANCE = """Evaluate achievements based on the candidate's domain with professional enterprise standards:

TECHNOLOGY & ENGINEERING:
- High value on Open-source contributions and Technical certifications.
- Value hackathon wins and internal recognition in large companies.
- Look for AWS, GCP, Azure, Kubernetes, or cloud certifications.

FINANCE & BANKING:
- High value on CFA, FRM, CPA, or other finance certifications.
- Look for trading competitions, stock pitch contests, or finance club leadership.
- Value relevant coursework certifications or Bloomberg Terminal proficiency.

CONSULTING:
- High value on case competition wins (McKinsey, BCG, Bain cups).
- Look for student consulting clubs, entrepreneurship centers, or business competitions.
- Leadership in clubs, organizations, or community service shows well-roundedness.

PRODUCT MANAGEMENT:
- Value product hackathons, design challenges, or user research projects.
- Look for leadership in student organizations or product-focused clubs.
- Entrepreneurship (side projects, startups) shows initiative.

MARKETING & GROWTH:
- Value marketing competitions, ad campaigns managed, or social media growth.
- Look for certifications in Google Ads, HubSpot, or social media tools.
- Content creation (blogs, YouTube, podcasts) demonstrates skills.

DATA SCIENCE & ML:
- High value on Kaggle competitions, hackathon wins, or research papers.
- Look for competitive programming (Codeforces, LeetCode) or math competitions.
- Value certifications from Coursera, edX, or deep learning courses.

SALES & BUSINESS DEVELOPMENT:
- Value sales competitions, business development challenges, or networking events.
- Look for leadership in clubs, entrepreneurship, or fundraising achievements.
- Sports or activities demonstrating persistence and goal orientation.

OPERATIONS & SUPPLY CHAIN:
- Value Lean Six Sigma certifications or process improvement projects.
- Look for operations challenges, supply chain competitions, or logistics projects.
- Leadership in clubs or community service shows well-roundedness.

Provide domain-appropriate evaluation of achievements and recommendations."""

BASE_ACHIEVEMENTS_PROMPT = """You are a senior recruiter specialized in professional enterprise roles. Analyze the achievements section below with production-grade enterprise expectations in mind.

Recruiter Perspective:
Evaluate achievements based on the candidate's domain with professional enterprise standards:

TECHNOLOGY & ENGINEERING:
- High value on Open-source contributions and Technical certifications.
- Value hackathon wins and internal recognition in large companies.
- Look for AWS, GCP, Azure, Kubernetes, or cloud certifications.

FINANCE & BANKING:
- High value on CFA, FRM, CPA, or other finance certifications.
- Look for trading competitions, stock pitch contests, or finance club leadership.
- Value relevant coursework certifications or Bloomberg Terminal proficiency.

CONSULTING:
- High value on case competition wins (McKinsey, BCG, Bain cups).
- Look for student consulting clubs, entrepreneurship centers, or business competitions.
- Leadership in clubs, organizations, or community service shows well-roundedness.

PRODUCT MANAGEMENT:
- Value product hackathons, design challenges, or user research projects.
- Look for leadership in student organizations or product-focused clubs.
- Entrepreneurship (side projects, startups) shows initiative.

MARKETING & GROWTH:
- Value marketing competitions, ad campaigns managed, or social media growth.
- Look for certifications in Google Ads, HubSpot, or social media tools.
- Content creation (blogs, YouTube, podcasts) demonstrates skills.

DATA SCIENCE & ML:
- High value on Kaggle competitions, hackathon wins, or research papers.
- Look for competitive programming (Codeforces, LeetCode) or math competitions.
- Value certifications from Coursera, edX, or deep learning courses.

SALES & BUSINESS DEVELOPMENT:
- Value sales competitions, business development challenges, or networking events.
- Look for leadership in clubs, entrepreneurship, or fundraising achievements.
- Sports or activities demonstrating persistence and goal orientation.

OPERATIONS & SUPPLY CHAIN:
- Value Lean Six Sigma certifications or process improvement projects.
- Look for operations challenges, supply chain competitions, or logistics projects.
- Leadership in clubs or community service shows well-roundedness.

Provide domain-appropriate evaluation of achievements and recommendations.

Analyze achievements:
1. Evaluate impact of each achievement based on professional enterprise standards.
2. Determine if it should be kept or removed.
3. Check for typos, grammar issues.
4. Verify relevance to a professional enterprise career path.

For achievements, return array:
[
  {
    "index": 0,
    "title": "Achievement title",
    "impact_score": number (0-10),
    "recommendation": "keep/remove",
    "reasoning": "explanation why keep or remove",
    "issues": ["issue1", "issue2"]
  }
]

Return a JSON object with:
{
    "achievements": [...],
    "suggestions": ["Specific feedback about achievements (e.g., 'Your competitive programming experience is a strong signal for high-tier roles. Highlighting your Codeforces rank prominently would help you stand out.')"],
    "score": number (out of 10)
}
"""


def get_achievements_prompt(tier: str = None) -> ChatPromptTemplate:
    """Get the achievements analysis prompt."""
    return ChatPromptTemplate.from_template(BASE_ACHIEVEMENTS_PROMPT)


def format_achievements_data(achievements, hobbies, extra_curricular):
    """Format achievements data for the LLM prompt."""
    import json
    return json.dumps([{"title": a.title, "descriptions": a.descriptions} for a in (achievements or [])], indent=2)