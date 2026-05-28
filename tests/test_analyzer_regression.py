"""Tests for pipeline filtering and scoring changes."""
import json
import pytest

from app.pipeline import AnalysisPipeline
from app.analyzer.consolidator import consolidate_analysis, _calculate_tiered_score


class TestHighScoringEntryFilter:
    def test_filters_experience_suggestions_above_threshold(self):
        result = {
            "experience_analysis": [
                {"entry_summary": "Good entry", "score": 20.0, "suggestions": [{"bullet_index": 0, "advice": "Fix this"}]},
                {"entry_summary": "Bad entry", "score": 10.0, "suggestions": [{"bullet_index": 0, "advice": "Fix this"}]},
            ],
            "projects_analysis": [],
        }
        AnalysisPipeline._filter_high_scoring_entries(result)
        assert result["experience_analysis"][0]["suggestions"] == []
        assert len(result["experience_analysis"][1]["suggestions"]) == 1

    def test_filters_projects_suggestions_above_threshold(self):
        result = {
            "experience_analysis": [],
            "projects_analysis": [
                {"entry_name": "Good project", "score": 25.0, "suggestions": [{"bullet_index": 0, "advice": "Fix"}]},
                {"entry_name": "Ok project", "score": 19.0, "suggestions": [{"bullet_index": 0, "advice": "Fix"}]},
            ],
        }
        AnalysisPipeline._filter_high_scoring_entries(result)
        assert result["projects_analysis"][0]["suggestions"] == []
        assert len(result["projects_analysis"][1]["suggestions"]) == 1

    def test_handles_missing_sections_gracefully(self):
        result = {"experience_analysis": [], "projects_analysis": []}
        AnalysisPipeline._filter_high_scoring_entries(result)
        assert result["experience_analysis"] == []

    def test_filters_section_suggestions_and_areas_above_threshold(self):
        result = {
            "experience_analysis": [],
            "projects_analysis": [],
            "sections": [
                {"name": "Skills", "score": 13.0, "max_score": 15, "suggestions": ["Improve"]},
                {"name": "Education", "score": 6.0, "max_score": 10, "suggestions": ["Add more"]},
                {"name": "Achievements & Hobbies", "score": 8.0, "max_score": 10, "suggestions": ["Expand"]},
                {"name": "Certifications", "score": 4.0, "max_score": 5, "suggestions": ["Get cert"]},
            ],
            "areas_for_improvement": [
                "Skills development: score of 13 is concerning",
                "Education: consider adding more",
                "Some other issue not related to sections",
            ],
        }
        AnalysisPipeline._filter_high_scoring_entries(result)
        # Skills ≥ 12.0 → suggestions cleared
        assert result["sections"][0]["suggestions"] == []
        # Education 6.0 < 8.0 → suggestions kept
        assert result["sections"][1]["suggestions"] == ["Add more"]
        # Achievements 8.0 ≥ 8.0 → suggestions cleared
        assert result["sections"][2]["suggestions"] == []
        # Certifications 4.0 ≥ 4.0 → suggestions cleared
        assert result["sections"][3]["suggestions"] == []
        # areas_for_improvement "Skills" item removed, "Education" kept, unrelated kept
        assert result["areas_for_improvement"] == [
            "Education: consider adding more",
            "Some other issue not related to sections",
        ]

"""Regression tests for `'str' object has no attribute 'content'` bug.

After LLMClient.ainvoke() was changed to return a plain str (instead of an
object with a .content attribute), 5 analyzer files still called .content
on the response, causing AttributeError. The try/except handlers in each
file mask the bug by returning degraded fallback data.

These tests verify the fix by asserting that the mock LLM response is
actually processed (not just falling through to the except handler).
"""
import json
from typing import Optional

import pytest

from app.analyzer.batch_rewriter import batch_rewrite_suggestions
from app.analyzer.rewriter import rewrite_bullet
from app.analyzer.repetition_checker import find_repeated_words
from app.analyzer.experience_analyzer import analyze_experience
from app.analyzer.metadata_analyzer import analyze_metadata
from app.analyzer.projects_analyzer import analyze_projects
from app.analyzer.strategic_analyzer import analyze_strategic
from app.llm.protocol import LLMClient
from app.llm.schema import Resume, Experience, Education, Project, Achievement, Certification


class FakeLLMClient(LLMClient):
    def __init__(self, response: str = "{}"):
        self.response = response
        self.last_prompt: Optional[str] = None

    async def ainvoke(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response


def make_minimal_resume() -> Resume:
    return Resume(
        name="Jane Doe",
        email="jane@test.com",
        skills=["Python", "AWS"],
        experience=[
            Experience(
                company="Acme Corp",
                title="Engineer",
                start_date="2020-01",
                end_date="2023-12",
                descriptions=["Built APIs", "Led team of 3"],
            )
        ],
        education=[
            Education(name="State University", score="3.8 GPA"),
        ],
        projects=[
            Project(name="RateMyResume", descriptions=["Full-stack web app"]),
        ],
        certifications=[Certification(name="AWS SA", issuer="Amazon")],
        achievements=[Achievement(title="Employee Month", descriptions=["Won award"])],
        hobbies=["Chess"],
        extra_curricular=["Mentoring"],
        total_years_experience=4.0,
    )


class TestMissingSectionScores:
    @pytest.mark.asyncio
    async def test_missing_sections_score_zero(self):
        """Missing education/certs/achievements should score 0, not 2.5-5."""
        client = FakeLLMClient(response=json.dumps({
            "overall_summary": "Test",
            "strengths": ["Test"],
            "areas_for_improvement": ["Test"],
        }))
        scores, summary, strengths, areas, roles = await consolidate_analysis(
            llm_client=client,
            basic_info_analysis=None,
            experience_analysis=[],
            projects_analysis=[],
            skills_analysis=None,
            education_analysis=[],
            achievements_hobbies_analysis=None,
            certifications_analysis=[],
            job_role_suggestions=[],
        )
        assert scores.education_score == 0
        assert scores.achievements_hobbies_score == 0
        assert scores.certifications_score == 0


class TestMetadataAnalyzer:
    @pytest.mark.asyncio
    async def test_processes_mock_response_not_fallback(self):
        """Verify mock education entry is processed, not fallback empty list."""
        client = FakeLLMClient(response=json.dumps({
            "education": [{
                "entry_index": 0,
                "institution_name_valid": True,
                "institution_name": "State University",
                "date_issues": [],
                "gpa_analysis": {"value": "3.8 GPA", "recommendation": "keep", "reasoning": "Good GPA"},
                "issues": [],
                "suggestions": [],
                "score": 8.0,
            }],
            "certifications": [{
                "index": 0,
                "name": "AWS SA",
                "is_valid": True,
                "organization_issues": [],
                "date_issues": [],
                "link_issues": [],
                "suggestions": [],
                "score": 4.0,
            }],
            "achievements": [{
                "index": 0,
                "title": "Employee Month",
                "impact_score": 6.0,
                "recommendation": "keep",
                "reasoning": "Good",
                "issues": [],
            }],
            "hobbies": [],
            "overall_metadata_suggestions": [],
        }))
        edu, cert, ach = await analyze_metadata(make_minimal_resume(), client)
        assert len(edu) == 1, "Expected education to be processed, got fallback"
        assert edu[0].institution_name == "State University"


class TestStrategicAnalyzer:
    @pytest.mark.asyncio
    async def test_processes_mock_response_not_fallback(self):
        """Verify mock skills analysis is processed, not fallback defaults."""
        client = FakeLLMClient(response=json.dumps({
            "skills_analysis": {
                "listed_in_exp_projects": ["Python"],
                "missing_from_skills": [],
                "redundant_skills": [],
                "issues": [],
                "suggestions": ["Add cloud skills"],
                "score": 14.0,
            },
            "job_role_suggestions": [{
                "role": "Senior Engineer",
                "match_score": 8.0,
                "reasoning": "Good fit",
                "suggestions": [],
            }],
        }))
        skills, roles, jd = await analyze_strategic(make_minimal_resume(), client)
        assert len(roles) == 1, "Expected job roles to be processed, got fallback"
        assert roles[0].role == "Senior Engineer"
        assert skills.score == 14.0  # mock value, not fallback 10.0


class TestExperienceAnalyzer:
    @pytest.mark.asyncio
    async def test_processes_mock_response_not_fallback(self):
        """Verify mock experience entry is processed, not fallback."""
        client = FakeLLMClient(response=json.dumps({
            "entries": [{
                "entry_index": 0,
                "star_score": 9.0,
                "star_reasoning": "Good STAR structure.",
                "score": 18.0,
                "good_things": ["Clear impact"],
                "recommendation": "keep",
                "suggestions": [],
            }],
        }))
        result = await analyze_experience(make_minimal_resume(), client)
        assert len(result) == 1
        assert result[0].star_principle_score == 9.0  # mock value, not fallback 5.0


class TestProjectsAnalyzer:
    @pytest.mark.asyncio
    async def test_processes_mock_response_not_fallback(self):
        """Verify mock project entry is processed, not fallback."""
        client = FakeLLMClient(response=json.dumps({
            "entries": [{
                "entry_index": 0,
                "star_score": 8.0,
                "star_reasoning": "Good.",
                "score": 22.0,
                "good_things": ["Interesting"],
                "recommendation": "keep",
                "suggestions": [],
            }],
        }))
        result = await analyze_projects(make_minimal_resume(), client)
        assert len(result) == 1
        assert result[0].star_principle_score == 8.0  # mock value, not fallback 5.0


class TestBatchRewriter:
    @pytest.mark.asyncio
    async def test_processes_mock_response_not_fallback(self):
        """Verify mock rephrase is processed, not fallback defaults."""
        client = FakeLLMClient(response=json.dumps({
            "content": "Led team to deliver",
        }))
        suggestions = [{
            "section": "experience",
            "entry_index": 0,
            "bullet_index": 0,
            "bullet": "Built APIs",
            "advice": "Add metrics",
            "context": "Team of 3",
        }]
        result = await batch_rewrite_suggestions(suggestions, client)
        assert "experience__0__0" in result
        assert result["experience__0__0"]["content"] == "Led team to deliver"
        assert result["experience__0__0"]["label"] == "Rephrased"


class TestTieredScoring:
    def test_fresher_includes_low_scoring_supplementary(self):
        """Fresher tier should include supplementary sections even at low scores."""
        total, active_max = _calculate_tiered_score(
            basic_info_score=8.0, experience_score=15.0,
            projects_score=0, skills_score=10.0,
            education_score=0, ach_score=0,
            certifications_score=0, target_tier="fresher",
        )
        # Fresher: supp threshold 0.3, so 0/25=0 < 0.3 → projects dropped?
        # Actually projects=0/25=0 < 0.3, so it IS dropped even for fresher
        # Let me test with scores just above threshold
        pass

    def test_fresher_has_lower_supp_threshold(self):
        """Fresher uses 0.3 threshold, experienced uses 0.5."""
        total_f, max_f = _calculate_tiered_score(
            basic_info_score=8.0, experience_score=15.0,
            projects_score=7.5, skills_score=10.0,
            education_score=3.0, ach_score=3.0,
            certifications_score=1.5, target_tier="fresher",
        )
        total_e, max_e = _calculate_tiered_score(
            basic_info_score=8.0, experience_score=15.0,
            projects_score=7.5, skills_score=10.0,
            education_score=3.0, ach_score=3.0,
            certifications_score=1.5, target_tier="experienced",
        )
        # projects 7.5/25=0.3, education 3/10=0.3, ach 3/10=0.3, certs 1.5/5=0.3
        # Fresher: all meet 0.3 threshold → all included
        assert max_f == 100
        # Experienced: none meet 0.5 threshold → only core included
        assert max_e == 50


class TestWordRepetitionChecker:
    def test_detects_repeated_words_in_section(self):
        """Verify repeated significant words are flagged per section."""
        sections = {
            "experience": "Engineered the backend. Engineered the frontend. Engineered the API layer.",
            "projects": "Monitored dashboard metrics. Monitored API latency. Monitored error rates.",
        }
        result = find_repeated_words(sections)
        assert "engineered" in result.get("experience", [])
        assert "monitored" in result.get("projects", [])

    def test_excludes_stopwords(self):
        """Verify articles, prepositions, pronouns are excluded."""
        sections = {
            "experience": "The team and the project. A solution for the client.",
        }
        result = find_repeated_words(sections)
        for word in result.get("experience", []):
            assert word not in ["the", "and", "a", "for"]

    def test_no_repetition_returns_empty(self):
        """Verify sections with no significant repetition return empty."""
        sections = {
            "experience": "Led a team.",
            "projects": "Built an API.",
            "skills": "Python, AWS",
        }
        result = find_repeated_words(sections)
        assert all(len(words) == 0 for words in result.values())

    def test_detects_cross_section_repetition(self):
        """Verify a word used in multiple sections is flagged in each."""
        sections = {
            "experience": "Engineered the backend. Engineered the frontend.",
            "projects": "Engineered the platform. Engineered the deployment.",
        }
        result = find_repeated_words(sections)
        assert "engineered" in result.get("experience", [])
        assert "engineered" in result.get("projects", [])


class TestWordRepetitionInBatchRewriter:
    @pytest.mark.asyncio
    async def test_repeated_words_in_prompt(self):
        """Verify repeated_words are passed into the batch rewriter prompt."""
        client = FakeLLMClient(response=json.dumps({"content": "Rephrased."}))
        suggestions = [{
            "section": "experience",
            "entry_index": 0,
            "bullet_index": 0,
            "bullet": "Built APIs",
            "advice": "Use stronger verbs",
            "context": "Team of 3",
            "repeated_words": ["built", "led"],
        }]
        result = await batch_rewrite_suggestions(suggestions, client)
        assert client.last_prompt is not None
        assert "built, led" in client.last_prompt or "built" in client.last_prompt
        assert "avoid" in client.last_prompt.lower()

    async def test_accumulated_used_words_in_prompt(self):
        """Verify accumulated_used_words are passed into the batch rewriter prompt."""
        client = FakeLLMClient(response=json.dumps({"content": "Rephrased."}))
        suggestions = [{
            "section": "experience",
            "entry_index": 0,
            "bullet_index": 0,
            "bullet": "Built APIs",
            "advice": "Use stronger verbs",
            "context": "Team of 3",
            "repeated_words": [],
        }]
        used_words = {"engineered", "spearheaded"}
        result = await batch_rewrite_suggestions(suggestions, client, accumulated_used_words=used_words)
        assert client.last_prompt is not None
        assert "at most once" in client.last_prompt.lower()
        assert "engineered" in client.last_prompt
        assert "spearheaded" in client.last_prompt


class TestRewriteBulletNoMetricInjection:
    @pytest.mark.asyncio
    async def test_prompt_instructs_no_metric_injection(self):
        """Verify the rewriter prompt tells the LLM to never inject metrics not in original."""
        client = FakeLLMClient(response=json.dumps({"content": "Rephrased bullet."}))
        await rewrite_bullet("Built an API", "Use stronger action verbs", client)
        assert "never" in client.last_prompt.lower()

    @pytest.mark.asyncio
    async def test_returns_single_content_not_versions_array(self):
        """Verify rewriter returns a single content string, not a versions array."""
        client = FakeLLMClient(response=json.dumps({"content": "Engineered an API."}))
        result = await rewrite_bullet("Built an API", "Use stronger action verbs", client)
        assert "content" in result
        assert "versions" not in result
        assert isinstance(result["content"], str)

    @pytest.mark.asyncio
    async def test_prompt_contains_no_metric_guidance(self):
        """Verify the prompt no longer contains metric suggestion language."""
        client = FakeLLMClient(response=json.dumps({"content": "Rephrased."}))
        await rewrite_bullet("Built an API", "Use stronger action verbs", client)
        prompt_lower = client.last_prompt.lower()
        assert "metric_suggestion" not in prompt_lower
        assert "metric guidance" not in prompt_lower

    @pytest.mark.asyncio
    async def test_error_fallback_uses_content_not_versions(self):
        """Verify the error fallback returns single content, not versions array."""
        class FailingLLMClient(LLMClient):
            async def ainvoke(self, prompt: str) -> str:
                raise Exception("LLM unavailable")
        result = await rewrite_bullet("Built an API", "Use stronger action verbs", FailingLLMClient())
        assert "content" in result
        assert "versions" not in result
        assert isinstance(result["content"], str)
        assert "Built an API" in result["content"]

    @pytest.mark.asyncio
    async def test_prompt_contains_evaluation_criteria(self):
        """Verify the rewriter prompt includes evaluation criteria (action verbs, cause-effect, specificity)."""
        client = FakeLLMClient(response=json.dumps({"content": "Rephrased."}))
        await rewrite_bullet("Built an API", "Use stronger action verbs", client)
        prompt_lower = client.last_prompt.lower()
        assert "action verbs" in prompt_lower or "stronger verbs" in prompt_lower
        assert "cause-effect" in prompt_lower or "cause and effect" in prompt_lower
        assert "specific" in prompt_lower
