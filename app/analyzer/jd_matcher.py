import json
from ..llm.client import llm
from .schemas import JDAnalysis


JD_MATCHER_PROMPT = """You are a senior technical recruiter and talent advisor.
Your task is to compare a candidate's resume against a specific Job Description (JD).

Be extremely critical and detailed. Don't just give a generic score. 
Look for:
1. Tech Stack Alignment: Exact technology matches vs. adjacent ones.
2. Experience Depth: Does the candidate have the required years/seniority for this specific JD?
3. Domain Knowledge: Match between candidate projects and JD domain (e.g., Fintech, AI, E-commerce).
4. Impact Match: Are the JD's core responsibilities reflected in the candidate's achievements?

Return a JSON object with:
{
    "match_score": number (0-100),
    "compatible_roles": ["Roles from the JD that the candidate fits"],
    "missing_critical_skills": ["Must-have skills from JD NOT in resume"],
    "missing_nice_to_have": ["Bonus skills from JD NOT in resume"],
    "tailoring_recommendations": [
        "Specific advice: 'The JD emphasizes AWS Lambda, but you only mentioned EC2 - highlight any serverless experience you have'",
        "Specific advice: 'This is a Senior role requiring mentorship, but your resume is purely individual contributor - add details on coaching juniors if applicable'"
    ]
}"""


def match_with_jd(resume, jd: str) -> JDAnalysis:
    """Compare resume with a specific job description"""
    if not jd:
        return None

    # Prepare context
    skills = resume.skills or []
    exp_titles = [f"{e.title} at {e.company}" for e in resume.experience or []]
    
    prompt = f"""{JD_MATCHER_PROMPT}

JOB DESCRIPTION:
{jd}

RESUME SUMMARY:
Name: {resume.name}
Skills: {json.dumps(skills)}
Experience: {json.dumps(exp_titles)}
Professional Summary: {resume.professional_summary or "None"}

Return a JSON object with the JD matching analysis."""

    try:
        response = llm.invoke(prompt)
        json_str = response.content.strip()

        # Clean up markdown
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        elif json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()

        data = json.loads(json_str)

        return JDAnalysis(
            match_score=data.get("match_score", 0.0),
            compatible_roles=data.get("compatible_roles", []),
            missing_critical_skills=data.get("missing_critical_skills", []),
            missing_nice_to_have=data.get("missing_nice_to_have", []),
            tailoring_recommendations=data.get("tailoring_recommendations", [])
        )

    except Exception as e:
        print(f"Error in JD matching: {e}")
        return None
