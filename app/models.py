from typing import List, Optional
from pydantic import BaseModel, Field


class PortfolioLinks(BaseModel):
    github: Optional[str] = Field(default=None, description="URL to GitHub profile")
    linkedin: Optional[str] = Field(default=None, description="URL to LinkedIn profile")
    personal_website: Optional[str] = Field(
        default=None, description="URL to portfolio or personal site"
    )
    other_links: List[str] = Field(
        default_factory=list, description="Any other relevant links found"
    )


class UniversityObject(BaseModel):
    name: str = Field(description="Name of the institution")
    score: Optional[str] = Field(
        default=None, description="GPA, percentage, or grade with units if available"
    )
    start_date: Optional[str] = Field(
        default=None, description="Start date of the degree"
    )
    end_date: Optional[str] = Field(
        default=None, description="Graduation date or expected graduation"
    )
    location: Optional[str] = Field(
        default=None, description="Location of the institution"
    )


class Project(BaseModel):
    name: str = Field(description="Name of the project")
    description: str = Field(
        description="The details and impact of the specific project"
    )
    technologies: List[str] = Field(
        default_factory=list, description="Technologies or tools used"
    )


class ExperienceEntry(BaseModel):
    role: str = Field(description="Job title or position")
    start_date: Optional[str] = Field(
        default=None, description="Start date of the role"
    )
    end_date: Optional[str] = Field(default=None, description="End date of the role")
    description: str = Field(
        description="Bullet points or paragraph describing the work performed"
    )
    organization: str = Field(description="Name of the organization/company")
    location: Optional[str] = Field(
        default=None, description="Location of the organization"
    )


class ExperienceWrapper(BaseModel):
    history: List[ExperienceEntry] = Field(
        default_factory=list, description="List of all previous and current work roles"
    )
    total_years_experience: float = Field(
        default=0.0, description="Calculated total years of professional experience"
    )


class ResumeDocument(BaseModel):
    name: str = Field(description="Full name of the applicant")
    email: str = Field(description="Email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    portfolio: PortfolioLinks = Field(
        default_factory=PortfolioLinks, description="Portfolio and social links"
    )
    education: List[UniversityObject] = Field(
        default_factory=list, description="Education history"
    )
    projects: List[Project] = Field(default_factory=list, description="Projects")
    experience: ExperienceWrapper = Field(
        default_factory=ExperienceWrapper, description="Work experience"
    )
    skills: List[str] = Field(
        default_factory=list, description="Technical and professional skills"
    )
    certifications: List[str] = Field(
        default_factory=list, description="Certifications"
    )
    achievements: List[str] = Field(default_factory=list, description="Achievements")
    hobbies: List[str] = Field(default_factory=list, description="Hobbies (optional)")
    extra_curricular: List[str] = Field(
        default_factory=list,
        description="Volunteer work, clubs, or non-professional activities",
    )


MAX_WEIGHTS = {
    "contact": 5,
    "experience": 20,
    "projects": 20,
    "skills": 8,
    "education": 5,
    "page_count": 5,
    "grammar": 5,
    "certificates": 5,
    "achievements": 5,
    "hobbies": 2,
}


class FeedbackItem(BaseModel):
    section: str = Field(
        description="Section name (e.g., experience, projects, skills)"
    )
    item_index: Optional[int] = Field(
        default=None,
        description="Index of the item within the section (None for section-level)",
    )
    issue: str = Field(default="", description="Description of the issue found")
    suggestion: str = Field(default="", description="How to fix the issue")
    score: float = Field(
        default=0.0, description="Score for this item (0 to max weight)"
    )
    max_score: float = Field(
        default=10.0, description="Maximum possible score for this item"
    )
    criteria: str = Field(
        default="", description="Criteria checked (e.g., STAR principle, grammar)"
    )


class FeedbackResponse(BaseModel):
    contact_feedback: List[FeedbackItem] = Field(default_factory=list)
    experience_feedback: List[FeedbackItem] = Field(default_factory=list)
    projects_feedback: List[FeedbackItem] = Field(default_factory=list)
    skills_feedback: List[FeedbackItem] = Field(default_factory=list)
    education_feedback: List[FeedbackItem] = Field(default_factory=list)
    overall_score: float = Field(default=0.0)
    summary: str = Field(default="")


class SectionScore(BaseModel):
    section: str = Field(description="Section name")
    max_weight: float = Field(
        default=0.0, description="Maximum weight for this section"
    )
    score: float = Field(default=0.0, description="Score earned in this section")
    feedback: List[FeedbackItem] = Field(
        default_factory=list, description="Feedback items for this section"
    )


class AnalysisResult(BaseModel):
    extracted_data: Optional[ResumeDocument] = Field(
        default=None, description="Structured extracted resume data"
    )
    base_score: float = Field(default=0.0, description="Base score (0-100)")
    bonus_score: float = Field(default=0.0, description="Bonus from optional sections")
    total_score: float = Field(default=0.0, description="Total score (can exceed 100)")
    section_scores: List[SectionScore] = Field(
        default_factory=list, description="Score breakdown by section"
    )
    page_count: int = Field(default=0, description="Number of pages in the resume")
    is_valid: bool = Field(
        default=True, description="Whether the resume was successfully parsed"
    )
    validation_errors: List[str] = Field(
        default_factory=list, description="Errors encountered during parsing"
    )
