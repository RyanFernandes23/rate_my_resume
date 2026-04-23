import sys

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv()

import time

print("Loading modules...")
t0 = time.time()

from app.extractors import extract
from app.llm import extract_resume

print(f"Modules loaded in {time.time() - t0:.1f}s")

print("\nStep 1: Extracting markdown from PDF...")
t1 = time.time()
markdown = extract("tests/Ryanfernandes (4).pdf")
print(f"Extracted {len(markdown)} characters in {time.time() - t1:.1f}s")

print("\nStep 2: Extracting resume with LLM...")
t2 = time.time()
resume = extract_resume(markdown)
print(f"Extracted in {time.time() - t2:.1f}s")

print("\n--- Extracted Resume ---")
print(f"Name: {resume.name}")
print(f"Email: {resume.email}")
print(f"Phone: {resume.phone}")
print(f"LinkedIn: {resume.linkedin}")
print(f"GitHub: {resume.github}")
print(f"Location: {resume.location}")
print(f"Summary: {resume.summary}")

print(f"\nSkills ({len(resume.skills)}): {resume.skills}")

print(f"\nExperience: {len(resume.experience)} entries")
for i, exp in enumerate(resume.experience):
    print(f"  {i + 1}. {exp.title} at {exp.company}")
    print(f"     {exp.start_date} - {exp.end_date}")
    for d in exp.descriptions:
        print(f"     - {d[:80]}...")

print(f"\nEducation: {len(resume.education)} entries")
for i, edu in enumerate(resume.education):
    print(f"  {i + 1}. {edu.name}")
    print(f"     Score: {edu.score}")
    print(f"     {edu.start_date} - {edu.end_date}")
    print(f"     Location: {edu.location}")

print(f"\nTotal Years Experience: {resume.total_years_experience}")

print(f"\nProjects: {len(resume.projects)} entries")
for i, proj in enumerate(resume.projects):
    print(f"  {i + 1}. {proj.name}")
    print(f"     Link: {proj.link}")
    for d in proj.descriptions:
        print(f"     - {d[:80]}...")

print(f"\nAchievements: {len(resume.achievements)} entries")
for i, ach in enumerate(resume.achievements):
    print(f"  {i + 1}. {ach.title}")
    print(f"     Descriptions: {ach.descriptions}")

print(f"\nCertifications: {len(resume.certifications)} entries")
for i, cert in enumerate(resume.certifications):
    print(f"  {i + 1}. {cert.name}")
    print(f"     Issuer: {cert.issuer}, Date: {cert.date}, Link: {cert.link}")

print(f"\nHobbies: {resume.hobbies}")
print(f"Extra Curricular: {resume.extra_curricular}")
