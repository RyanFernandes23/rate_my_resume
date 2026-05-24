import sys

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv()

import time
import json

print("Loading modules...")
t0 = time.time()

from app.extractors import extract
from app.llm import extract_resume
from app.analyzer import analyze_resume

print(f"Modules loaded in {time.time() - t0:.1f}s")

print("\n" + "=" * 50)
print("STEP 1: Extracting Resume from PDF")
print("=" * 50)

t1 = time.time()
markdown = extract("tests/Ryanfernandes (4).pdf")
print(f"Extracted markdown: {len(markdown)} characters in {time.time() - t1:.1f}s")

print("\n" + "=" * 50)
print("STEP 2: Parsing Resume Data")
print("=" * 50)

t2 = time.time()
resume = extract_resume(markdown)
print(f"Parsed resume in {time.time() - t2:.1f}s")

print(f"\n--- Extracted Data ---")
print(f"Name: {resume.name}")
print(f"Email: {resume.email}")
print(f"Skills: {len(resume.skills)} items")
print(f"Experience: {len(resume.experience)} entries")
print(f"Projects: {len(resume.projects)} entries")

print("\n" + "=" * 50)
print("STEP 3: Analyzing Resume")
print("=" * 50)

import asyncio
t3 = time.time()
analysis = asyncio.run(analyze_resume(resume))
print(f"Analyzed resume in {time.time() - t3:.1f}s")

print("\n" + "=" * 50)
print("SCORE BREAKDOWN")
print("=" * 50)
sb = analysis.score_breakdown
print(f"Basic Info:      {sb.basic_info_score}/10 ({sb.basic_info_score * 10:.1f}%)")
print(f"Experience:      {sb.experience_score}/25 ({sb.experience_score * 4:.1f}%)")
print(f"Projects:        {sb.projects_score}/25 ({sb.projects_score * 4:.1f}%)")
print(f"Skills:          {sb.skills_score}/15 ({sb.skills_score * 6.67:.1f}%)")
print(f"Education:       {sb.education_score}/10 ({sb.education_score * 10:.1f}%)")
print(f"Job Role Fit:     Not Scored (Just Suggestions)")
print(f"-" * 30)
print(f"TOTAL:           {sb.total_score}/100 ({sb.total_percentage:.1f}%)")
print(f"Converted Score: {sb.converted_percentage}/100")

print("\n" + "=" * 50)
print("JOB ROLE SUGGESTIONS")
print("=" * 50)
for role in analysis.job_role_suggestions[:5]:
    print(f"\n{role.role}")
    print(f"  Match Score: {role.match_score}/10")
    print(f"  Reasoning: {role.reasoning[:150]}...")

print("\n" + "=" * 50)
print("OVERALL SUMMARY")
print("=" * 50)
print(analysis.overall_summary)

print("\n" + "=" * 50)
print("STRENGTHS")
print("=" * 50)
for s in analysis.strengths:
    print(f"- {s}")

print("\n" + "=" * 50)
print("AREAS FOR IMPROVEMENT")
print("=" * 50)
for a in analysis.areas_for_improvement:
    print(f"- {a}")

print("\n" + "=" * 50)
print("EXPERIENCE ANALYSIS")
print("=" * 50)
for exp in analysis.experience_analysis:
    print(f"\n{exp.entry_summary}")
    print(f"  Score: {exp.score}/25")
    print(f"  STAR Score: {exp.star_principle_score}/10")
    print(f"  Impact Score: {exp.impact_score}/10")
    print(f"  Recommendation: {exp.recommendation}")
    if exp.suggestions:
        print(f"  Suggestions:")
        for s in exp.suggestions[:2]:
            print(f"    - {s.advice[:100]}...")

print("\n" + "=" * 50)
print("PROJECTS ANALYSIS")
print("=" * 50)
for proj in analysis.projects_analysis:
    print(f"\n{proj.entry_name}")
    print(f"  Score: {proj.score}/25")
    if proj.suggestions:
        print(f"  Suggestions:")
        for s in proj.suggestions[:2]:
            print(f"    - {s.advice[:100]}...")

print("\n" + "=" * 50)
print("SKILLS ANALYSIS")
print("=" * 50)
sa = analysis.skills_analysis
print(f"Total Skills: {sa.total_count}")
print(f"Missing from Skills: {len(sa.missing_from_skills)}")
if sa.missing_from_skills:
    print(f"  {sa.missing_from_skills[:5]}")
print(f"Redundant Skills: {len(sa.redundant_skills)}")
print(f"Score: {sa.score}/15")

print("\n" + "=" * 50)
print("EDUCATION ANALYSIS")
print("=" * 50)
for edu in analysis.education_analysis:
    print(f"\n{edu.institution_name}")
    print(f"  Score: {edu.score}/10")
    print(f"  GPA: {edu.gpa_analysis.value} - {edu.gpa_analysis.recommendation}")

print("\n" + "=" * 50)
print("CERTIFICATIONS ANALYSIS")
print("=" * 50)
for cert in analysis.certifications_analysis:
    print(f"\n{cert.name}")
    print(f"  Valid: {cert.is_valid}")
    print(f"  Score: {cert.score}/5")

print("\n[OK] Analysis Complete!")
