from pydantic import BaseModel, Field
from typing import Optional


class Experience(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    descriptions: list[str] = []


class Education(BaseModel):
    name: Optional[str] = None  # Original field, will hold institution for backward compatibility
    degree: Optional[str] = None
    institution: Optional[str] = None
    score: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None


class Project(BaseModel):
    name: Optional[str] = None
    descriptions: list[str] = []
    link: Optional[str] = None


class Achievement(BaseModel):
    title: Optional[str] = None
    descriptions: list[str] = []


class Certification(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    date: Optional[str] = None
    link: Optional[str] = None


class Resume(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    location: Optional[str] = None
    professional_summary: Optional[str] = None
    summary: Optional[str] = None
    links: list[str] = []
    experience: list[Experience] = []
    total_years_experience: Optional[float] = None
    education: list[Education] = []
    skills: list[str] = []
    projects: list[Project] = []
    achievements: list[Achievement] = []
    certifications: list[Certification] = []
    hobbies: list[str] = []
    extra_curricular: list[str] = []
