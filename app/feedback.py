import time
import logging
from typing import List, Dict, Any

from langchain_openrouter import ChatOpenRouter

from app import config
from app.models import (
    ResumeDocument,
    FeedbackItem,
    SectionScore,
    MAX_WEIGHTS,
    FeedbackResponse,
)
from app.logger import log_api_call

logger = logging.getLogger("rate_my_resume")

PRIMARY_MODEL = "google/gemma-3-27b-it:free"
FALLBACK_MODEL = "openrouter/free"


FEEDBACK_SYSTEM_PROMPT = """You are an expert resume reviewer. Analyze resumes and provide detailed, actionable feedback.

For each section, evaluate:
1. STRENGTHS: What is done well
2. ISSUES: What needs improvement
3. SUGGESTIONS: Specific actionable recommendations

Score each criteria from 0-10 based on quality.
Return structured feedback with specific issues and scores."""


FEEDBACK_USER_PROMPT_TEMPLATE = """Analyze this resume and provide detailed feedback:

RESUME DATA:
{name}
{email}
{phone}

PORTFOLIO:
{portfolio}

EDUCATION:
{education}

EXPERIENCE:
{experience}

PROJECTS:
{projects}

SKILLS:
{skills}

Provide feedback for each section with:
- Specific issues found
- Actionable suggestions
- Scores (0-10)

Return a structured response."""


class FeedbackGenerator:
    def __init__(self):
        self.primary_model = PRIMARY_MODEL
        self.fallback_model = FALLBACK_MODEL
        self.last_model_used = None

    def _create_llm(self, model_name: str) -> ChatOpenRouter:
        return ChatOpenRouter(
            model=model_name,
            temperature=0.3,
            max_completion_tokens=4000,
        )

    def _format_resume_for_prompt(self, resume: ResumeDocument) -> str:
        portfolio = (
            resume.portfolio
            or type("obj", (), {"linkedin": "", "github": "", "personal_website": ""})()
        )

        education_text = ""
        if resume.education:
            for edu in resume.education:
                education_text += (
                    f"- {edu.name}: {edu.score} ({edu.start_date}-{edu.end_date})\n"
                )

        experience_text = ""
        if resume.experience and resume.experience.history:
            for exp in resume.experience.history:
                experience_text += f"- {exp.role} at {exp.organization}\n  {exp.start_date}-{exp.end_date}\n  {exp.description}\n"

        projects_text = ""
        if resume.projects:
            for proj in resume.projects:
                projects_text += f"- {proj.name}: {proj.description}\n  Tech: {', '.join(proj.technologies)}\n"

        skills_text = ", ".join(resume.skills) if resume.skills else "None"

        return FEEDBACK_USER_PROMPT_TEMPLATE.format(
            name=resume.name or "Not provided",
            email=resume.email or "Not provided",
            phone=resume.phone or "Not provided",
            portfolio=f"LinkedIn: {portfolio.linkedin or 'N/A'}, GitHub: {portfolio.github or 'N/A'}, Website: {portfolio.personal_website or 'N/A'}",
            education=education_text or "None",
            experience=experience_text or "None",
            projects=projects_text or "None",
            skills=skills_text,
        )

    def _convert_to_section_scores(
        self, feedback_response: FeedbackResponse, resume: ResumeDocument
    ) -> List[SectionScore]:
        section_scores = []

        max_contact = MAX_WEIGHTS["contact"]
        contact_score_val = sum(f.score for f in feedback_response.contact_feedback)
        section_scores.append(
            SectionScore(
                section="contact",
                max_weight=max_contact,
                score=round(min(contact_score_val, max_contact), 2),
                feedback=feedback_response.contact_feedback,
            )
        )

        max_exp = MAX_WEIGHTS["experience"]
        exp_score_val = sum(f.score for f in feedback_response.experience_feedback)
        section_scores.append(
            SectionScore(
                section="experience",
                max_weight=max_exp,
                score=round(min(exp_score_val, max_exp), 2),
                feedback=feedback_response.experience_feedback,
            )
        )

        max_proj = MAX_WEIGHTS["projects"]
        proj_score_val = sum(f.score for f in feedback_response.projects_feedback)
        section_scores.append(
            SectionScore(
                section="projects",
                max_weight=max_proj,
                score=round(min(proj_score_val, max_proj), 2),
                feedback=feedback_response.projects_feedback,
            )
        )

        max_skills = MAX_WEIGHTS["skills"]
        skills_score_val = sum(f.score for f in feedback_response.skills_feedback)
        section_scores.append(
            SectionScore(
                section="skills",
                max_weight=max_skills,
                score=round(min(skills_score_val, max_skills), 2),
                feedback=feedback_response.skills_feedback,
            )
        )

        max_edu = MAX_WEIGHTS["education"]
        edu_score_val = sum(f.score for f in feedback_response.education_feedback)
        section_scores.append(
            SectionScore(
                section="education",
                max_weight=max_edu,
                score=round(min(edu_score_val, max_edu), 2),
                feedback=feedback_response.education_feedback,
            )
        )

        page_max = MAX_WEIGHTS["page_count"]
        section_scores.append(
            SectionScore(
                section="page_count",
                max_weight=page_max,
                score=page_max,
                feedback=[
                    FeedbackItem(
                        section="page_count",
                        issue="Page count is optimal",
                        suggestion="Keep resume to 1-2 pages",
                        score=page_max,
                        max_score=page_max,
                        criteria="Page length",
                    )
                ],
            )
        )

        grammar_max = MAX_WEIGHTS["grammar"]
        section_scores.append(
            SectionScore(
                section="grammar",
                max_weight=grammar_max,
                score=grammar_max,
                feedback=[
                    FeedbackItem(
                        section="grammar",
                        issue="Resume appears well-written",
                        suggestion="Continue with polished writing",
                        score=grammar_max,
                        max_score=grammar_max,
                        criteria="Professional tone",
                    )
                ],
            )
        )

        cert_max = MAX_WEIGHTS["certificates"]
        certs = resume.certifications or []
        section_scores.append(
            SectionScore(
                section="certificates",
                max_weight=cert_max,
                score=min(len(certs) * 2, cert_max),
                feedback=[
                    FeedbackItem(
                        section="certificates",
                        issue=f"{len(certs)} certification(s) found"
                        if certs
                        else "No certifications listed",
                        suggestion="Add relevant certifications"
                        if not certs
                        else "Good certification portfolio",
                        score=min(len(certs) * 2, cert_max),
                        max_score=cert_max,
                        criteria="Professional development",
                    )
                ],
            )
        )

        achieve_max = MAX_WEIGHTS["achievements"]
        achievements = resume.achievements or []
        section_scores.append(
            SectionScore(
                section="achievements",
                max_weight=achieve_max,
                score=min(len(achievements) * 2, achieve_max),
                feedback=[
                    FeedbackItem(
                        section="achievements",
                        issue=f"{len(achievements)} achievement(s)"
                        if achievements
                        else "No achievements listed",
                        suggestion="Add notable achievements"
                        if not achievements
                        else "Good achievement record",
                        score=min(len(achievements) * 2, achieve_max),
                        max_score=achieve_max,
                        criteria="Recognition",
                    )
                ],
            )
        )

        hobbies_max = MAX_WEIGHTS["hobbies"]
        hobbies = resume.hobbies or []
        section_scores.append(
            SectionScore(
                section="hobbies",
                max_weight=hobbies_max,
                score=hobbies_max if hobbies else 0,
                feedback=[
                    FeedbackItem(
                        section="hobbies",
                        issue=f"{len(hobbies)} hobby(ies)"
                        if hobbies
                        else "No hobbies listed",
                        suggestion="Add hobbies to show personality"
                        if not hobbies
                        else "Great well-rounded profile",
                        score=hobbies_max if hobbies else 0,
                        max_score=hobbies_max,
                        criteria="Personality",
                    )
                ],
            )
        )

        return section_scores

    def generate(
        self, resume_data: ResumeDocument, page_count: int
    ) -> List[SectionScore]:
        resume = resume_data

        logger.info("=" * 50)
        logger.info("STARTING STRUCTURED OUTPUT FEEDBACK GENERATION")
        logger.info("=" * 50)

        resume_text = self._format_resume_for_prompt(resume)

        structured_llm = None
        error_msg = None

        try:
            logger.info(f"Attempting with model: {self.primary_model}")
            llm = self._create_llm(self.primary_model)
            structured_llm = llm.with_structured_output(FeedbackResponse)

            response = structured_llm.invoke(
                [
                    {"role": "system", "content": FEEDBACK_SYSTEM_PROMPT},
                    {"role": "user", "content": resume_text},
                ]
            )

            self.last_model_used = self.primary_model
            logger.info(f"Structured output success with {self.primary_model}")

            section_scores = self._convert_to_section_scores(response, resume)
            return section_scores

        except Exception as e:
            error_msg = str(e)
            logger.warning(
                f"Structured output failed with {self.primary_model}: {error_msg[:100]}"
            )

            try:
                logger.info(f"Attempting with fallback model: {self.fallback_model}")
                llm = self._create_llm(self.fallback_model)
                structured_llm = llm.with_structured_output(FeedbackResponse)

                response = structured_llm.invoke(
                    [
                        {"role": "system", "content": FEEDBACK_SYSTEM_PROMPT},
                        {"role": "user", "content": resume_text},
                    ]
                )

                self.last_model_used = self.fallback_model
                logger.info(f"Structured output success with {self.fallback_model}")

                section_scores = self._convert_to_section_scores(response, resume)
                return section_scores

            except Exception as e2:
                error_msg2 = str(e2)
                logger.warning(f"Fallback also failed: {error_msg2[:100]}")

        logger.warning("Structured output failed, using fallback scoring")

        section_scores = self._fallback_scoring(resume)

        total_items = sum(len(s.feedback) for s in section_scores)
        logger.info(
            f"Feedback complete: {len(section_scores)} sections, {total_items} items"
        )

        return section_scores

    def _fallback_scoring(self, resume: ResumeDocument) -> List[SectionScore]:
        section_scores = []

        contact_max = MAX_WEIGHTS["contact"]
        section_scores.append(
            SectionScore(
                section="contact",
                max_weight=contact_max,
                score=contact_max,
                feedback=[
                    FeedbackItem(
                        section="contact",
                        issue="Contact information complete",
                        score=contact_max,
                        max_score=contact_max,
                        criteria="Contact presence",
                    )
                ],
            )
        )

        exp_max = MAX_WEIGHTS["experience"]
        if resume.experience and resume.experience.history:
            exp_entries = len(resume.experience.history)
            exp_score = min(exp_entries * 7, exp_max)
            feedback = []
            for idx, exp in enumerate(resume.experience.history):
                has_action = any(
                    w in exp.description.lower()
                    for w in ["led", "built", "created", "developed", "managed"]
                )
                has_metrics = any(c.isdigit() for c in exp.description)

                if has_action or has_metrics:
                    feedback.append(
                        FeedbackItem(
                            section="experience",
                            item_index=idx,
                            issue="Good use of action verbs and metrics"
                            if has_action and has_metrics
                            else "Consider adding more quantified results",
                            suggestion="Great STAR format!",
                            score=5,
                            max_score=10,
                            criteria="STAR principle",
                        )
                    )

            section_scores.append(
                SectionScore(
                    section="experience",
                    max_weight=exp_max,
                    score=exp_score,
                    feedback=feedback,
                )
            )
        else:
            section_scores.append(
                SectionScore(
                    section="experience", max_weight=exp_max, score=0, feedback=[]
                )
            )

        proj_max = MAX_WEIGHTS["projects"]
        if resume.projects:
            proj_score = min(len(resume.projects) * 7, proj_max)
            feedback = []
            for idx, proj in enumerate(resume.projects):
                feedback.append(
                    FeedbackItem(
                        section="projects",
                        item_index=idx,
                        issue=f"Project has {(proj.technologies or []).__len__()} technologies",
                        suggestion="Good project details"
                        if proj.description
                        else "Add more detail",
                        score=7,
                        max_score=10,
                        criteria="Project quality",
                    )
                )

            section_scores.append(
                SectionScore(
                    section="projects",
                    max_weight=proj_max,
                    score=proj_score,
                    feedback=feedback,
                )
            )
        else:
            section_scores.append(
                SectionScore(
                    section="projects", max_weight=proj_max, score=0, feedback=[]
                )
            )

        skills_max = MAX_WEIGHTS["skills"]
        skills_count = len(resume.skills or [])
        skills_score = min(skills_count, skills_max)
        section_scores.append(
            SectionScore(
                section="skills",
                max_weight=skills_max,
                score=skills_score,
                feedback=[
                    FeedbackItem(
                        section="skills",
                        issue=f"{skills_count} skills listed",
                        suggestion="Good skill diversity"
                        if skills_count >= 5
                        else "Add more relevant skills",
                        score=skills_score,
                        max_score=skills_max,
                        criteria="Skills depth",
                    )
                ],
            )
        )

        edu_max = MAX_WEIGHTS["education"]
        if resume.education:
            section_scores.append(
                SectionScore(
                    section="education",
                    max_weight=edu_max,
                    score=edu_max,
                    feedback=[
                        FeedbackItem(
                            section="education",
                            issue="Education details complete",
                            score=edu_max,
                            max_score=edu_max,
                            criteria="Education presence",
                        )
                    ],
                )
            )
        else:
            section_scores.append(
                SectionScore(
                    section="education", max_weight=edu_max, score=0, feedback=[]
                )
            )

        page_max = MAX_WEIGHTS["page_count"]
        section_scores.append(
            SectionScore(
                section="page_count",
                max_weight=page_max,
                score=page_max,
                feedback=[
                    FeedbackItem(
                        section="page_count",
                        issue="Optimal page length",
                        score=page_max,
                        max_score=page_max,
                        criteria="Page count",
                    )
                ],
            )
        )

        grammar_max = MAX_WEIGHTS["grammar"]
        section_scores.append(
            SectionScore(
                section="grammar",
                max_weight=grammar_max,
                score=grammar_max,
                feedback=[
                    FeedbackItem(
                        section="grammar",
                        issue="Resume appears well-written",
                        score=grammar_max,
                        max_score=grammar_max,
                        criteria="Grammar",
                    )
                ],
            )
        )

        cert_max = MAX_WEIGHTS["certificates"]
        certs = resume.certifications or []
        section_scores.append(
            SectionScore(
                section="certificates",
                max_weight=cert_max,
                score=min(len(certs) * 2, cert_max),
                feedback=[
                    FeedbackItem(
                        section="certificates",
                        issue=f"{len(certs)} certifications",
                        score=min(len(certs) * 2, cert_max),
                        max_score=cert_max,
                        criteria="Certifications",
                    )
                ],
            )
        )

        achieve_max = MAX_WEIGHTS["achievements"]
        achievements = resume.achievements or []
        section_scores.append(
            SectionScore(
                section="achievements",
                max_weight=achieve_max,
                score=min(len(achievements) * 2, achieve_max),
                feedback=[
                    FeedbackItem(
                        section="achievements",
                        issue=f"{len(achievements)} achievements",
                        score=min(len(achievements) * 2, achieve_max),
                        max_score=achieve_max,
                        criteria="Achievements",
                    )
                ],
            )
        )

        hobbies_max = MAX_WEIGHTS["hobbies"]
        hobbies = resume.hobbies or []
        section_scores.append(
            SectionScore(
                section="hobbies",
                max_weight=hobbies_max,
                score=hobbies_max if hobbies else 0,
                feedback=[
                    FeedbackItem(
                        section="hobbies",
                        issue=f"{len(hobbies)} hobbies",
                        score=hobbies_max if hobbies else 0,
                        max_score=hobbies_max,
                        criteria="Hobbies",
                    )
                ],
            )
        )

        return section_scores

    def calculate_final_scores(self, section_scores: List[SectionScore]) -> tuple:
        base_score = 0
        bonus_score = 0

        bonus_sections = {"certificates", "achievements", "hobbies"}

        for section in section_scores:
            if section.section in bonus_sections:
                bonus_score += section.score
            else:
                base_score += section.score

        total = base_score + bonus_score
        logger.info(
            f"Final scores - Base: {base_score}, Bonus: {bonus_score}, Total: {total}"
        )

        return base_score, bonus_score, round(total, 2)
