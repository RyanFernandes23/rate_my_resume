"""Tests for pipeline filtering and scoring changes."""
import json
import pytest

from app.pipeline import AnalysisPipeline
from app.analyzer.consolidator import consolidate_analysis


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
        """Verify mock rewrites are processed, not fallback defaults."""
        client = FakeLLMClient(response=json.dumps({
            "rewrites": [{"label": "Action-Oriented", "content": "Led team to deliver"}],
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
        # Fallback produces generic text, mock produces our exact content
        assert "experience__0__0" in result
        assert result["experience__0__0"][0]["content"] == "Led team to deliver"
