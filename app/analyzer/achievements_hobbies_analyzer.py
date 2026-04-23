import json
from ..llm.client import llm
from .schemas import AchievementsHobbiesAnalysis, AchievementAnalysis, HobbyAnalysis


ACHIEVEMENTS_HOBBIES_PROMPT = """You are a resume analysis expert specializing in achievements and hobbies evaluation.

Analyze achievements:
1. Evaluate impact of each achievement
2. Determine if it should be kept or removed
3. Check for typos, grammar issues
4. Verify relevance to career

For achievements, return array:
[{
    "index": 0,
    "title": "Achievement title",
    "impact_score": number (0-10),
    "recommendation": "keep/remove",
    "reasoning": "explanation why keep or remove",
    "issues": ["issue1", "issue2"]
}]

Analyze hobbies:
1. Determine if hobby is professional (relates to job/career)
2. Consider removing very common/unprofessional hobbies
3. Check for typos

For hobbies, return array:
[{
    "hobby": "hobby name",
    "is_professional": true/false,
    "suggestions": ["suggestion if needed"]
}]

Return a JSON object with:
{
    "achievements": [...],
    "hobbies": [...],
    "suggestions": ["suggest something IF the score is < 10, e.g. 'Add certifications' or 'Quantify your awards'"],
    "score": number (out of 10)
}

IMPORTANT: If the user has empty achievements, suggest specific things they likely have but didn't list (e.g. 'Dean's List', 'Open Source contributions', 'Certifications from Coursera/Udemy').

Scoring:
- Achievements count for 6 marks, Hobbies for 4 marks
- Keep meaningful achievements with impact
- Professional hobbies add value, common ones can be omitted
- Empty achievements or hobbies is acceptable (neutral score)"""


def analyze_achievements_hobbies(resume) -> AchievementsHobbiesAnalysis:
    """Analyze achievements and hobbies (combined node)"""

    # Prepare data
    achievements = resume.achievements or []
    hobbies = resume.hobbies or []
    extra_curricular = resume.extra_curricular or []

    # Combine extra_curricular with hobbies for analysis
    all_hobbies = hobbies + extra_curricular

    prompt = f"""{ACHIEVEMENTS_HOBBIES_PROMPT}

Achievements:
{json.dumps([{"title": a.title, "descriptions": a.descriptions} for a in achievements], indent=2)}

Hobbies/Extra-curricular:
{json.dumps(all_hobbies, indent=2)}

Return a JSON object with the analysis."""

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

        analysis = json.loads(json_str)

        # Convert achievements
        ach_results = []
        for ach in analysis.get("achievements", []):
            ach_results.append(
                AchievementAnalysis(
                    index=ach.get("index", 0),
                    title=ach.get("title", ""),
                    impact_score=ach.get("impact_score", 5.0),
                    recommendation=ach.get("recommendation", "keep"),
                    reasoning=ach.get("reasoning", ""),
                    issues=ach.get("issues", []),
                )
            )

        # Convert hobbies
        hobby_results = []
        for hb in analysis.get("hobbies", []):
            hobby_results.append(
                HobbyAnalysis(
                    hobby=hb.get("hobby", ""),
                    is_professional=hb.get("is_professional", False),
                    suggestions=hb.get("suggestions", []),
                )
            )

        return AchievementsHobbiesAnalysis(
            achievements=ach_results,
            hobbies=hobby_results,
            suggestions=analysis.get("suggestions", []),
            score=analysis.get("score", 5.0),
        )

    except Exception as e:
        # Fallback
        return AchievementsHobbiesAnalysis(
            achievements=[
                AchievementAnalysis(
                    index=i,
                    title=a.title,
                    impact_score=5.0,
                    recommendation="keep",
                    reasoning="Unable to analyze",
                    issues=["Could not analyze"],
                )
                for i, a in enumerate(achievements)
            ],
            hobbies=[
                HobbyAnalysis(hobby=h, is_professional=False, suggestions=[])
                for h in all_hobbies
            ],
            score=5.0,
        )
