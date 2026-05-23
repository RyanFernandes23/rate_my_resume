from .schemas import (
    BasicInfoAnalysis,
    FieldAnalysis,
    LinksAnalysis,
    AnalysisIssue,
)


ANALYZER_SYSTEM_PROMPT = """You are a resume analysis expert. Analyze the given resume section and provide detailed feedback with scores.

For each analysis:
1. Validate the field/value
2. Identify issues with severity (high/medium/low)
3. Provide specific suggestions with reasoning
4. Score based on criteria

Always provide reasoning for your scores and suggestions."""


def analyze_basic_info(resume) -> BasicInfoAnalysis:
    """Analyze name, email, phone, and links"""

    # Name analysis
    name_issues = []
    name_suggestions = []
    name_valid = True

    if not resume.name:
        name_issues.append(
            AnalysisIssue(
                issue="Name is missing",
                severity="high",
                reason="Name is a required field in any resume",
            )
        )
        name_valid = False
        name_suggestions.append("Hey, I noticed your name is missing. You should add your full name at the top of the resume so recruiters know who you are!")
    elif len(resume.name.split()) < 2:
        name_issues.append(
            AnalysisIssue(
                issue="Only first name provided",
                severity="medium",
                reason="Full name (first and last) is standard for professional resumes",
            )
        )
        name_suggestions.append(
            "Hey, you only provided your first name. Adding your last name is important for a complete professional identity."
        )

    name_analysis = FieldAnalysis(
        is_valid=name_valid,
        current_value=resume.name,
        issues=name_issues,
        suggestions=name_suggestions,
    )

    # Email analysis
    email_issues = []
    email_suggestions = []
    email_valid = True

    if not resume.email:
        email_issues.append(
            AnalysisIssue(
                issue="Email is missing",
                severity="high",
                reason="Email is required for employer contact",
            )
        )
        email_valid = False
        email_suggestions("Add a professional email address")
    elif resume.email:
        # Basic email format check
        import re

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, resume.email):
            email_issues.append(
                AnalysisIssue(
                    issue="Invalid email format",
                    severity="high",
                    reason="Email format appears incorrect",
                )
            )
            email_valid = False
            email_suggestions.append(
                "Check email for typos, ensure format like: name@example.com"
            )
        elif any(
            word in resume.email.lower() for word in ["test", "fake", "dummy", "123"]
        ):
            email_issues.append(
                AnalysisIssue(
                    issue="Email appears to be a placeholder",
                    severity="high",
                    reason="Professional email expected",
                )
            )
            email_valid = False
            email_suggestions.append(
                "Hey, this email looks like a placeholder. You should use a professional email address like firstname.lastname@gmail.com."
            )

    email_analysis = FieldAnalysis(
        is_valid=email_valid,
        current_value=resume.email,
        issues=email_issues,
        suggestions=email_suggestions,
    )

    # Phone analysis
    phone_issues = []
    phone_suggestions = []
    phone_valid = True

    if not resume.phone:
        phone_issues.append(
            AnalysisIssue(
                issue="Phone number is missing",
                severity="high",
                reason="Phone is required for employer contact",
            )
        )
        phone_valid = False
        phone_suggestions.append("Hey, I can't find your phone number. Adding a contact number with your country code is essential for recruiters to reach you.")
    elif resume.phone:
        # Check for reasonable phone format
        import re

        phone_digits = re.sub(r"\D", "", resume.phone)
        if len(phone_digits) < 10:
            phone_issues.append(
                AnalysisIssue(
                    issue="Phone number appears incomplete",
                    severity="medium",
                    reason="Phone number should have at least 10 digits",
                )
            )
            phone_valid = False
            phone_suggestions.append("Ensure phone number includes area code")
        elif not any(c.isdigit() for c in resume.phone):
            phone_issues.append(
                AnalysisIssue(
                    issue="Phone number contains no digits",
                    severity="high",
                    reason="Phone number must contain digits",
                )
            )
            phone_valid = False

    phone_analysis = FieldAnalysis(
        is_valid=phone_valid,
        current_value=resume.phone,
        issues=phone_issues,
        suggestions=phone_suggestions,
    )

    # Links analysis
    links_issues = []
    links_suggestions = []
    current_links = []
    missing_important = []
    links_valid = True

    if resume.linkedin:
        current_links.append(f"LinkedIn: {resume.linkedin}")
        if not resume.linkedin.startswith("http"):
            links_issues.append(
                AnalysisIssue(
                    issue="LinkedIn URL is incomplete",
                    severity="high",
                    reason="LinkedIn URL should be a full URL starting with https://",
                )
            )
            links_valid = False
            links_suggestions.append(
                "Add full LinkedIn URL: https://linkedin.com/in/yourprofile"
            )
    else:
        missing_important.append("LinkedIn profile")

    if resume.github:
        current_links.append(f"GitHub: {resume.github}")
        if not resume.github.startswith("http"):
            links_issues.append(
                AnalysisIssue(
                    issue="GitHub URL is incomplete",
                    severity="medium",
                    reason="GitHub URL should be a full URL",
                )
            )
            links_valid = False
    else:
        missing_important.append("GitHub profile (if you have projects)")

    if resume.links:
        current_links.extend(resume.links)

    # Check if at least contact links are present
    if not resume.linkedin and not resume.github and not resume.links:
        links_valid = False
        links_issues.append(
            AnalysisIssue(
                issue="No professional links provided",
                severity="medium",
                reason="At least LinkedIn or GitHub is recommended",
            )
        )
        links_suggestions.append(
            "Hey, I don't see any professional links. You should add your LinkedIn and GitHub profiles to showcase your work and network."
        )

    links_analysis = LinksAnalysis(
        is_valid=links_valid,
        current_links=current_links,
        missing_important_links=missing_important,
        broken_links=[],
        issues=links_issues,
        suggestions=links_suggestions,
    )

    # Calculate score (out of 10)
    # Base 10, subtract heavily for critical missing info
    base_score = 10.0

    # Name issues (Critical)
    if not name_valid:
        base_score -= 4.0
    elif any(i.severity == "medium" for i in name_issues):
        base_score -= 1.0

    # Email issues (Critical)
    if not email_valid:
        base_score -= 4.0
    elif any(i.severity == "medium" for i in email_issues):
        base_score -= 1.0

    # Phone issues (High)
    if not phone_valid:
        base_score -= 3.0
    elif any(i.severity == "medium" for i in phone_issues):
        base_score -= 1.0

    # Links issues (Medium)
    if not links_valid:
        base_score -= 2.0
    elif missing_important:
        # Penalize for each missing important link
        base_score -= (0.5 * len(missing_important))

    score = max(0, base_score)

    return BasicInfoAnalysis(
        name=name_analysis,
        email=email_analysis,
        phone=phone_analysis,
        links=links_analysis,
    )
