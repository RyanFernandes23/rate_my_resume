from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import tempfile
import os
import logging
import traceback
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

from app.extractors import extract
from app.llm import extract_resume
from app.analyzer import analyze_resume
from app.analyzer.schemas import ResumeAnalysis
from app.llm.schema import Resume
from app.routers import auth, credits, payments

app = FastAPI(title="Rate My Resume API")

app.include_router(auth.router)
app.include_router(credits.router)
app.include_router(payments.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def check_user_credits(user_id: str) -> int:
    """Check user's current credit balance"""
    from app.db import service_supabase
    
    response = (
        service_supabase.table("user_credits")
        .select("credits")
        .eq("user_id", user_id)
        .execute()
    )
    
    if response.data:
        return response.data[0]["credits"]
    return 0


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
        
        if rpc_result.data and rpc_result.data[0].get("success", False):
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
            "suggestions": list(
                dict.fromkeys(
                    [
                        s
                        for exp in (analysis.experience_analysis or [])
                        for s in exp.suggestions
                    ]
                )
            ),
        },
        {
            "name": "Projects",
            "score": sb.projects_score,
            "max_score": 15,
            "suggestions": list(
                dict.fromkeys(
                    [
                        s
                        for proj in (analysis.projects_analysis or [])
                        for s in proj.suggestions
                    ]
                )
            ),
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
                "suggestions": exp.suggestions,
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
                "suggestions": proj.suggestions,
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
    authorization: Optional[str] = Header(None),
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
    # STEP 1: AUTHENTICATION
    # ============================================================
    user_id = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        try:
            from jose import jwt
            from app.db import settings

            payload = jwt.decode(
                token, settings.supabase_jwt_secret, algorithms=["HS256"]
            )
            user_id = payload.get("sub")
            logger.info(f"Authenticated user: {user_id}")
        except Exception as e:
            logger.warning(f"Token verification failed: {e}")
    
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
    credits_before = None
    if user_id:
        credits_before = check_user_credits(user_id)
        logger.info(f"User {user_id} credits before analysis: {credits_before}")
        
        if credits_before < 1:
            logger.warning(f"Insufficient credits for user {user_id}")
            raise HTTPException(
                status_code=402, 
                detail={"error": "insufficient_credits", "credits": credits_before}
            )
    
    # ============================================================
    # STEP 4: PROCESS RESUME
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
        # STEP 5: DEDUCT CREDIT (Only after successful analysis)
        # ============================================================
        if user_id:
            success = deduct_user_credit(user_id, f"Resume analysis: {file.filename}")
            if not success:
                logger.error(f"Failed to deduct credit for user {user_id}")
                # Continue anyway - we can handle this async later
            else:
                credit_deducted = True
                credits_after = check_user_credits(user_id)
                logger.info(f"User {user_id} credits after analysis: {credits_after}")
        
        logger.info(
            f"Response prepared with "
            f"{len(result.get('job_role_suggestions', []))} job suggestions"
        )
        
        return JSONResponse(content=result)
    
    except HTTPException:
        # Re-raise HTTP exceptions (like 402) without modification
        raise
        
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error during analysis: {str(e)}\n{error_trace}")
        
        # ============================================================
        # STEP 6: REFUND CREDIT ON FAILURE
        # ============================================================
        if user_id and not credit_deducted:
            # Credit wasn't deducted yet, so no refund needed
            pass
        elif user_id and credit_deducted:
            # Credit was deducted, but analysis failed - REFUND
            logger.warning(f"Refunding credit to user {user_id} due to analysis failure")
            refund_user_credit(user_id, f"Analysis failed: {str(e)[:100]}")
        
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to analyze resume: {str(e)}"
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

    result = rewrite_bullet(request.bullet, request.suggestion, request.target_tier)
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)