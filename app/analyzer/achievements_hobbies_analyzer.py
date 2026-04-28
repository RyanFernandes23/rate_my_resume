"""Achievements and hobbies analyzer using LangChain and externalized prompts."""
import json
from ..llm.client import llm
from ..analyzer.schemas import AchievementsHobbiesAnalysis, AchievementAnalysis, HobbyAnalysis
from .prompts.achievements_prompts import get_achievements_prompt, format_achievements_data


def analyze_achievements_hobbies(resume, tier="STANDARD"):
    """Analyze achievements and hobbies (combined node) using externalized prompts."""
    # Prepare data
    achievements = resume.achievements or []
    hobbies = resume.hobbies or []
    extra_curricular = resume.extra_curricular or []

    # Combine extra_curricular with hobbies for analysis
    all_hobbies = hobbies + extra_curricular

    # Use LangChain prompt template
    prompt = get_achievements_prompt(tier)
    formatted_data = format_achievements_data(achievements, hobbies, extra_curricular)
    formatted_prompt = prompt.format(
        achievements_data=formatted_data["achievements_data"],
        hobbies_data=formatted_data["hobbies_data"],
    )

    try:
        response = llm.invoke(formatted_prompt)
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

        # Convert achievements with actual scoring
        ach_results = []
        ach_count = len(analysis.get("achievements", []))

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

        # Convert hobbies with actual scoring
        hobby_results = []
        hobby_count = len(analysis.get("hobbies", []))

        for hb in analysis.get("hobbies", []):
            hobby_results.append(
                HobbyAnalysis(
                    hobby=hb.get("hobby", ""),
                    is_professional=hb.get("is_professional", False),
                    suggestions=hb.get("suggestions", []),
                )
            )

        # Calculate actual score based on what's present
        # Achievements: 6pts (0.75pt each for up to 4)
        ach_score = min(6.0, ach_count * 0.75) if ach_count > 0 else 0.0

        # Hobbies: 4pts (1pt each for up to 4, but penalize if none)
        if hobby_count == 0 and ach_count == 0:
            # Both missing - very strict - low score
            hobby_score = 2.0
        else:
            hobby_score = min(4.0, hobby_count * 1.0)

        calculated_score = ach_score + hobby_score

        suggestions = analysis.get("suggestions", [])

        if ach_count == 0:
            suggestions.insert(0, "Add at least one concrete achievement (e.g., Dean's List, Kaggle competition rank, published research, open source contribution)")

        return AchievementsHobbiesAnalysis(
            achievements=ach_results,
            hobbies=hobby_results,
            suggestions=suggestions,
            score=round(calculated_score, 2),
        )

    except Exception as e:
        # Fallback with stricter scoring
        return _fallback_achievements_analysis(achievements, all_hobbies, e)


def _fallback_achievements_analysis(achievements, all_hobbies, error):
    """Fallback analysis when LLM fails."""
    ach_count = len(achievements)
    hobby_count = len(all_hobbies)

    # Achievements: 6pts (0.75pt each for up to 4)
    ach_score = min(6.0, ach_count * 0.75) if ach_count > 0 else 0.0

    # Hobbies: 4pts (1pt each for up to 4, but penalize if none)
    if hobby_count == 0 and ach_count == 0:
        hobby_score = 2.0  # Both missing - strict
    else:
        hobby_score = min(4.0, hobby_count * 1.0)

    calculated_score = ach_score + hobby_score

    suggestions = []
    if ach_count == 0:
        suggestions.append("Add at least one concrete achievement (e.g., Dean's List, Kaggle competition rank, published research, open source contribution)")

    return AchievementsHobbiesAnalysis(
        achievements=[
            AchievementAnalysis(
                index=i,
                title=a.title,
                impact_score=min(10.0, (i + 1) * 2.5),
                recommendation="keep",
                reasoning="Unable to analyze - based on available data",
                issues=["Could not analyze - LLM error"],
            )
            for i, a in enumerate(achievements)
        ],
        hobbies=[
            HobbyAnalysis(hobby=h, is_professional=False, suggestions=[])
            for h in all_hobbies
        ],
        suggestions=suggestions,
        score=round(calculated_score, 2),
    )
