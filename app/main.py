from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import tempfile
import os
import logging
import traceback
import re
import hashlib
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

from app.db import settings
from app.extractors import extract
from app.llm import extract_resume
from app.analyzer import analyze_resume
from app.analyzer.schemas import ResumeAnalysis
from app.llm.schema import Resume
from app.routers import auth, credits, payments, history
from app.dependencies import verify_premium_user, get_optional_user

app = FastAPI(title="Rate My Resume API")

app.include_router(auth.router)
app.include_router(credits.router)
app.include_router(payments.router)
app.include_router(history.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)


# Moved to app.dependencies


def deduct_user_credit(user_id: str, description: str = "Resume analysis") -> bool:
    """Deduct 1 credit from user's balance"""
    from app.db import service_supabase
    
    try:
        rpc_result = service_supabase.rpc(
            "use_credit", 
            {
                "p_user_id": user_id, 
                "p_description": description
            }
        ).execute()
        
        if rpc_result.data and isinstance(rpc_result.data, dict) and rpc_result.data.get("success", False):
            logger.info(f"Credit deducted for user {user_id}")
            return True
        else:
            logger.error(f"Failed to deduct credit for user {user_id}")
            return False
    except Exception as e:
        logger.error(f"Error deducting credit: {e}")
        return False


def refund_user_credit(user_id: str, reason: str = "Analysis failed") -> bool:
    """Refund 1 credit to user's balance"""
    from app.db import service_supabase
    
    try:
        rpc_result = service_supabase.rpc(
            "add_credits",
            {
                "p_user_id": user_id,
                "p_amount": 1,
                "p_type": "refund",
                "p_description": reason,
                "p_metadata": {"refunded_at": datetime.utcnow().isoformat()}
            }
        ).execute()
        
        if rpc_result.data:
            logger.info(f"Credit refunded for user {user_id}: {reason}")
            return True
        else:
            logger.error(f"Failed to refund credit for user {user_id}")
            return False
    except Exception as e:
        logger.error(f"Error refunding credit: {e}")
        return False


def transform_to_frontend_format(
    analysis: ResumeAnalysis, resume: Resume = None, page_count: int = 1
) -> dict:
    """Transform analyzer output to match frontend expected format"""

    sb = analysis.score_breakdown

    # Validation errors
    validation_errors = []
    if analysis.basic_info_analysis:
        if not analysis.basic_info_analysis.name.is_valid:
            validation_errors.append("Name is missing or invalid")
        if not analysis.basic_info_analysis.email.is_valid:
            validation_errors.append("Email is missing or invalid")
        if not analysis.basic_info_analysis.phone.is_valid:
            validation_errors.append("Phone is missing or invalid")

    # Check for missing sections
    if not analysis.skills_analysis or analysis.skills_analysis.total_count == 0:
        validation_errors.append("No skills found")

    # Helper to get all suggestions from basic info
    bi = analysis.basic_info_analysis
    bi_suggestions = []
    if bi:
        bi_suggestions.extend(bi.name.suggestions or [])
        bi_suggestions.extend(bi.email.suggestions or [])
        bi_suggestions.extend(bi.phone.suggestions or [])
        bi_suggestions.extend(bi.links.suggestions or [])

    # Sections analysis for frontend
    sections = [
        {
            "name": "Basic Information",
            "score": sb.basic_info_score,
            "max_score": 10,
            "suggestions": list(dict.fromkeys(bi_suggestions)),
        },
        {
            "name": "Experience",
            "score": sb.experience_score,
            "max_score": 25,
            "suggestions": [],  # Per-entry suggestions are now nested in experience_analysis
        },
        {
            "name": "Projects",
            "score": sb.projects_score,
            "max_score": 15,
            "suggestions": [],  # Per-entry suggestions are now nested in projects_analysis
        },
        {
            "name": "Skills",
            "score": sb.skills_score,
            "max_score": 15,
            "suggestions": analysis.skills_analysis.suggestions
            if analysis.skills_analysis
            else [],
        },
        {
            "name": "Education",
            "score": sb.education_score,
            "max_score": 10,
            "suggestions": list(
                dict.fromkeys(
                    [
                        s
                        for edu in (analysis.education_analysis or [])
                        for s in edu.suggestions
                    ]
                )
            ),
        },
        {
            "name": "Achievements & Hobbies",
            "score": sb.achievements_hobbies_score,
            "max_score": 10,
            "suggestions": analysis.achievements_hobbies_analysis.suggestions
            if analysis.achievements_hobbies_analysis
            else [],
        },
        {
            "name": "Certifications",
            "score": sb.certifications_score,
            "max_score": 5,
            "suggestions": list(
                dict.fromkeys(
                    [
                        s
                        for cert in (analysis.certifications_analysis or [])
                        for s in cert.suggestions
                    ]
                )
            ),
        },
    ]

    return {
        "total_score": sb.total_score,
        "total_percentage": sb.converted_percentage,
        "score_breakdown": {
            "basic_info_score": sb.basic_info_score,
            "experience_score": sb.experience_score,
            "projects_score": sb.projects_score,
            "skills_score": sb.skills_score,
            "education_score": sb.education_score,
            "achievements_hobbies_score": sb.achievements_hobbies_score,
            "certifications_score": sb.certifications_score,
            "job_role_fit_score": sb.job_role_fit_score,
            "total_score": sb.total_score,
            "total_percentage": sb.total_percentage,
            "converted_percentage": sb.converted_percentage,
            "benchmark_grade": sb.benchmark_grade,
            "target_tier": sb.target_tier,
        },
        "is_valid": len(validation_errors) == 0,
        "validation_errors": validation_errors,
        "strengths": analysis.strengths,
        "areas_for_improvement": analysis.areas_for_improvement,
        "sections": sections,
        "experience_analysis": [
            {
                "entry_summary": exp.entry_summary,
                "star_score": exp.star_principle_score,
                "impact_score": exp.impact_score,
                "recommendation": exp.recommendation,
                "suggestions": [
                    {
                        "bullet_index": s.bullet_index,
                        "original_bullet": s.original_bullet,
                        "context": s.context,
                        "advice": s.advice
                    }
                    for s in exp.suggestions
                ],
                "good_things": exp.good_things,
                "score": exp.score,
            }
            for exp in (analysis.experience_analysis or [])
        ],
        "projects_analysis": [
            {
                "entry_name": proj.entry_name,
                "star_score": proj.star_principle_score,
                "impact_score": proj.impact_score,
                "recommendation": proj.recommendation,
                "suggestions": [
                        {
                            "bullet_index": s.bullet_index,
                            "original_bullet": s.original_bullet,
                            "context": s.context,
                            "advice": s.advice
                        }
                        for s in proj.suggestions
                    ],
                "good_things": proj.good_things,
                "score": proj.score,
            }
            for proj in (analysis.projects_analysis or [])
        ],
        "job_role_suggestions": [
            {
                "role": role.role,
                "match_score": role.match_score,
                "reasoning": role.reasoning,
                "suggestions": role.suggestions,
            }
            for role in (analysis.job_role_suggestions or [])
        ],
        "benchmark_grade": sb.benchmark_grade,
        "target_tier": sb.target_tier,
        "jd_analysis": {
            "match_score": analysis.jd_analysis.match_score,
            "compatible_roles": analysis.jd_analysis.compatible_roles,
            "missing_critical_skills": analysis.jd_analysis.missing_critical_skills,
            "missing_nice_to_have": analysis.jd_analysis.missing_nice_to_have,
            "tailoring_recommendations": analysis.jd_analysis.tailoring_recommendations,
        }
        if analysis.jd_analysis
        else None,
    }


@app.get("/")
def root():
    return {"message": "Rate My Resume API"}


@app.post("/api/analyze")
async def analyze_resume_endpoint(
    file: UploadFile = File(...),
    jd: Optional[str] = None,
    target_tier: str = "Standard Enterprise",
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """
    Analyze a resume PDF or DOCX file with optional JD and target tier.
    Credit flow:
    1. Validate file
    2. Check credits (don't deduct yet)
    3. Process resume
    4. Deduct credit only after successful analysis
    5. Refund if analysis fails
    """
    
    # ============================================================
    # STEP 1: AUTH & CREDIT CHECK
    # ============================================================
    user_id = current_user.get("id") if current_user else None
    
    if user_id:
        from app.dependencies import check_user_credits
        credits_before = check_user_credits(user_id)
        if credits_before < 1:
            raise HTTPException(
                status_code=402, 
                detail={"error": "insufficient_credits", "credits": credits_before}
            )
        logger.info(f"User {user_id} starting analysis with {credits_before} credits")
    
    # ============================================================
    # STEP 2: FILE VALIDATION (Do this BEFORE touching credits)
    # ============================================================
    if not file.filename.lower().endswith((".pdf", ".docx")):
        logger.warning(f"Invalid file type: {file.filename}")
        raise HTTPException(
            status_code=400, 
            detail="Only PDF and DOCX files are supported"
        )
    
    # Read file content
    content = await file.read()
    
    # Check file size (10MB limit)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum size is 10MB"
        )
    
    # ============================================================
    # STEP 3: CREDIT CHECK (Without deducting)
    # ============================================================
    tmp_path = None
    credit_deducted = False
    
    try:
        # Save file temporarily
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=os.path.splitext(file.filename)[1]
        ) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        def process_resume_sync():
            logger.info(f"Step 1: Extracting markdown from {file.filename}")
            markdown = extract(tmp_path)
            logger.info(f"Extracted {len(markdown)} characters")
            
            if len(markdown) < 50:
                raise ValueError("Could not extract meaningful text from file")
            
            logger.info("Step 2: Parsing resume with LLM")
            resume = extract_resume(markdown)
            logger.info(
                f"Parsed resume: {resume.name}, "
                f"Skills: {len(resume.skills)}, "
                f"Experience: {len(resume.experience)}"
            )
            
            logger.info(
                f"Step 3: Analyzing resume (Tier: {target_tier}, "
                f"JD Provided: {bool(jd)})"
            )
            analysis = analyze_resume(resume, jd=jd, target_tier=target_tier)
            logger.info(
                f"Analysis complete. Score: {analysis.score_breakdown.total_score}/90"
            )
            
            logger.info("Step 4: Transforming to frontend format")
            result = transform_to_frontend_format(analysis, resume=resume, page_count=1)
            
            # ============================================================
            # STEP 5: EXTRACT ACTIONABLE SUGGESTIONS FOR BATCH REWRITE
            # ============================================================
            actionable_suggestions = []
            for section in result.get('sections', []):
                if section['name'] in ('Experience', 'Projects'):
                    section_key = section['name'].lower()
                    for entry_idx, entry in enumerate(result.get(f'{section_key}_analysis', [])):
                        # Handle both structured (new) and string (legacy) formats
                        for bullet_idx, sug_item in enumerate(entry.get('suggestions', [])):
                            if isinstance(sug_item, dict):
                                # New structured format: {bullet_index, original_bullet, context, suggestion}
                                actionable_suggestions.append({
                                    "section": section_key,
                                    "entry_index": entry_idx,
                                    "bullet_index": sug_item.get("bullet_index", bullet_idx),
                                    "bullet": sug_item.get("original_bullet", ""),
                                    "context": sug_item.get("context"),
                                    "advice": sug_item.get("advice", "")
                                })
                            else:
                                # Legacy string format - extract with regex
                                match = re.search(r'["\'](.*?)["\']', str(sug_item))
                                if match:
                                    original_bullet = match.group(1)
                                else:
                                    original_bullet = str(sug_item)
                                actionable_suggestions.append({
                                    "section": section_key,
                                    "entry_index": entry_idx,
                                    "bullet_index": bullet_idx,
                                    "bullet": original_bullet,
                                    "advice": str(sug_item)
                                })
            
            if actionable_suggestions:
                logger.info(f"Found {len(actionable_suggestions)} actionable suggestions to rewrite")
                from app.analyzer.batch_rewriter import batch_rewrite_suggestions
                rewrites = batch_rewrite_suggestions(actionable_suggestions, tier=target_tier)
                
                for sug in actionable_suggestions:
                    section_key = sug['section']
                    entry_idx = sug['entry_index']
                    bullet_idx = sug['bullet_index']

                    # Validate indices before accessing
                    section_analysis = result.get(f'{section_key}_analysis', [])
                    if entry_idx >= len(section_analysis):
                        logger.warning(f"Skipping rewrite - entry_idx {entry_idx} out of range for {section_key}")
                        continue
                    
                    entry_suggestions = section_analysis[entry_idx].get('suggestions', [])
                    if bullet_idx >= len(entry_suggestions):
                        logger.warning(f"Skipping rewrite - bullet_idx {bullet_idx} out of range for entry {entry_idx}")
                        continue
                    
                    # Enrich dict-formatted suggestions with rewrites (don't skip!)
                    if isinstance(entry_suggestions[bullet_idx], dict):
                        entry_suggestions[bullet_idx]["rewrites"] = rewrites.get(
                            f"{section_key}__{entry_idx}__{bullet_idx}", []
                        )
                    elif isinstance(entry_suggestions[bullet_idx], str):
                        entry_suggestions[bullet_idx] = {
                            "original_bullet": sug['bullet'],
                            "advice": entry_suggestions[bullet_idx],
                            "rewrites": rewrites.get(f"{section_key}__{entry_idx}__{bullet_idx}", [])
                        }
            return result
        
        from fastapi.concurrency import run_in_threadpool
        result = await run_in_threadpool(process_resume_sync)
        
        # ============================================================
        # STEP 6: DEDUCT CREDIT LAST (Only after successful analysis)
        # This ensures users only pay when we actually deliver value
        # ============================================================
        credit_deducted = False
        if user_id:
            try:
                success = deduct_user_credit(user_id, f"Resume analysis: {file.filename}")
                if not success:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to process payment. Please try again."
                    )
                credit_deducted = True
            except Exception as e:
                # Credit deduction failed AFTER analysis - this is critical
                logger.error(f"Failed to deduct credit after successful analysis: {e}")
                # Still return the result, but log the issue
                # User got the value, we just can't charge them - don't save to history
        
        # ============================================================
        # STEP 7: SAVE ANALYSIS TO SUPABASE (After credit attempt)
        # ============================================================
        analysis_id = None
        credits_after = None
        if user_id and credit_deducted:
            try:
                from app.db import service_supabase
                insert_data = {
                    "user_id": user_id,
                    "file_name": file.filename,
                    "target_tier": target_tier,
                    "jd_hash": hashlib.md5(jd.encode()).hexdigest() if jd else None,
                    "result_json": result
                }
                db_response = service_supabase.table("analyses").insert(insert_data).execute()
                if db_response.data:
                    analysis_id = db_response.data[0]["id"]
                    logger.info(f"Analysis saved with id {analysis_id}")
                
                # Also get updated credits
                credits_after = check_user_credits(user_id)
                logger.info(f"User {user_id} credits after analysis: {credits_after}")
            except Exception as e:
                logger.error(f"Failed to save analysis or fetch credits: {e}")
                # Analysis delivered but not saved - don't throw, user got value
        
        logger.info(
            f"Response prepared with "
            f"{len(result.get('job_role_suggestions', []))} job suggestions"
        )
        
        result_for_frontend = {
            "analysis_id": analysis_id,
            "analysis_data": result,
            "saved_to_history": bool(analysis_id),
            "remaining_credits": credits_after
        }
        
        return JSONResponse(content=result_for_frontend)
    
    except ValueError as e:
        # Specific validation errors that users can understand
        error_msg = str(e)
        if "exceeds" in error_msg.lower() or "pages" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail={"error": "page_limit", "message": error_msg}
            )
        raise HTTPException(status_code=400, detail=str(e))
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error during analysis: {str(e)}\n{error_trace}")
        
        # ============================================================
        # NO REFUND NEEDED
        # Credit is only deducted AFTER successful analysis
        # If we hit error here, credit was never deducted
        # ============================================================
        
        raise HTTPException(
            status_code=500, 
            detail="Failed to analyze resume. Please try again."
        )
        
    finally:
        # Clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                logger.debug(f"Cleaned up temp file: {tmp_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {e}")


class RewriteRequest(BaseModel):
    bullet: str
    suggestion: str
    target_tier: str = "Standard Enterprise"


@app.post("/api/rewrite")
async def rewrite_bullet_endpoint(request: RewriteRequest):
    from .analyzer.rewriter import rewrite_bullet
    from fastapi.concurrency import run_in_threadpool

    def run_rewrite_sync():
        return rewrite_bullet(request.bullet, request.suggestion, request.target_tier)

    result = await run_in_threadpool(run_rewrite_sync)
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)