from pydantic import BaseModel, Field
from typing import Optional, List


class AnalysisIssue(BaseModel):
    issue: str
    severity: str  # high, medium, low
    reason: str


class FieldAnalysis(BaseModel):
    is_valid: bool
    current_value: Optional[str] = None
    issues: List[AnalysisIssue] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class LinksAnalysis(BaseModel):
    is_valid: bool
    current_links: List[str] = Field(default_factory=list)
    missing_important_links: List[str] = Field(default_factory=list)
    broken_links: List[str] = Field(default_factory=list)
    issues: List[AnalysisIssue] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class BasicInfoAnalysis(BaseModel):
    name: FieldAnalysis
    email: FieldAnalysis
    phone: FieldAnalysis
    links: LinksAnalysis


class BulletSuggestion(BaseModel):
    bullet_index: int
    original_bullet: str
    suggestion: str


class ExperienceAnalysis(BaseModel):
    entry_index: int
    entry_summary: str  # "Company - Role"
    bullet_count: int
    bullet_length_avg: float
    star_principle_score: float  # 0-10
    star_principle_reasoning: str
    has_quantifiable_metrics: bool
    metrics_count: int
    impact_score: float  # 0-10
    issues: List[AnalysisIssue] = Field(default_factory=list)
    suggestions: List[BulletSuggestion] = Field(default_factory=list)  # Structured suggestions
    good_things: List[str] = Field(default_factory=list)
    recommendation: str  # keep/revise/remove
    score: float  # /25


class ProjectsAnalysis(BaseModel):
    entry_index: int
    entry_name: str
    bullet_count: int
    bullet_length_avg: float
    star_principle_score: float  # 0-10
    star_principle_reasoning: str
    has_quantifiable_metrics: bool
    metrics_count: int
    impact_score: float  # 0-10
    issues: List[AnalysisIssue] = Field(default_factory=list)
    suggestions: List[BulletSuggestion] = Field(default_factory=list)  # Structured suggestions
    good_things: List[str] = Field(default_factory=list)
    recommendation: str  # keep/revise/remove
    score: float  # /15


class SkillsAnalysis(BaseModel):
    total_count: int
    skills_list: List[str] = Field(default_factory=list)
    listed_in_exp_projects: List[str] = Field(
        default_factory=list
    )  # skills that appear in exp/proj
    missing_from_skills: List[str] = Field(
        default_factory=list
    )  # used in exp/proj but not listed
    redundant_skills: List[str] = Field(default_factory=list)  # listed but never used
    issues: List[AnalysisIssue] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    score: float  # /15


class GpaAnalysis(BaseModel):
    value: Optional[str] = None
    recommendation: str  # keep/remove
    reasoning: str


class EducationAnalysis(BaseModel):
    entry_index: int
    institution_name_valid: bool
    institution_name: str
    date_issues: List[str] = Field(default_factory=list)
    gpa_analysis: GpaAnalysis
    issues: List[AnalysisIssue] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    score: float  # /10
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None


class AchievementAnalysis(BaseModel):
    index: int
    title: str
    impact_score: float  # 0-10
    recommendation: str  # keep/remove
    reasoning: str
    issues: List[str] = Field(default_factory=list)


class HobbyAnalysis(BaseModel):
    hobby: str
    is_professional: bool  # relates to job/career
    suggestions: List[str] = Field(default_factory=list)


class AchievementsHobbiesAnalysis(BaseModel):
    achievements: List[AchievementAnalysis] = Field(default_factory=list)
    hobbies: List[HobbyAnalysis] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    score: float  # /10


class CertificationAnalysis(BaseModel):
    index: int
    name: str
    is_valid: bool
    organization_issues: List[str] = Field(default_factory=list)
    date_issues: List[str] = Field(default_factory=list)
    link_issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    score: float  # /5


class JobRoleSuggestion(BaseModel):
    role: str
    match_score: float  # 0-10
    reasoning: str
    suggestions: List[str] = Field(default_factory=list)


class JDAnalysis(BaseModel):
    match_score: float  # 0-100
    compatible_roles: List[str] = Field(default_factory=list)
    missing_critical_skills: List[str] = Field(default_factory=list)
    missing_nice_to_have: List[str] = Field(default_factory=list)
    tailoring_recommendations: List[str] = Field(default_factory=list)


class ScoreBreakdown(BaseModel):
    basic_info_score: float  # /10
    experience_score: float  # /25
    projects_score: float  # /15
    skills_score: float  # /15
    education_score: float  # /10
    achievements_hobbies_score: float  # /10
    certifications_score: float  # /5
    job_role_fit_score: float  # /10 (not scored, just suggestions)
    total_score: float  # /90 (actual scored)
    total_percentage: float  # out of 90
    converted_percentage: float  # out of 100
    benchmark_grade: Optional[str] = None  # e.g., "L5 / Senior Ready"
    target_tier: Optional[str] = None  # e.g., "Big Tech"


class ResumeAnalysis(BaseModel):
    score_breakdown: ScoreBreakdown
    basic_info_analysis: BasicInfoAnalysis
    experience_analysis: List[ExperienceAnalysis] = Field(default_factory=list)
    projects_analysis: List[ProjectsAnalysis] = Field(default_factory=list)
    skills_analysis: SkillsAnalysis
    education_analysis: List[EducationAnalysis] = Field(default_factory=list)
    achievements_hobbies_analysis: AchievementsHobbiesAnalysis
    certifications_analysis: List[CertificationAnalysis] = Field(default_factory=list)
    job_role_suggestions: List[JobRoleSuggestion] = Field(default_factory=list)
    overall_summary: str
    strengths: List[str] = Field(default_factory=list)
    areas_for_improvement: List[str] = Field(default_factory=list)
    jd_analysis: Optional[JDAnalysis] = None
