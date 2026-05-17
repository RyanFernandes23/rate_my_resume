from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional
import tempfile
import os
import logging
import traceback
import re
import hashlib
from datetime import datetime
import asyncio
import json

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
from app.routers.auth import get_current_user

app = FastAPI(title="Rate My Resume API")

app.include_router(auth.router)
app.include_router(credits.router)
app.include_router(payments.router)
app.include_router(history.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)


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


# Import transform_to_frontend_format from utils to avoid circular imports
from app.utils import transform_to_frontend_format


@app.get("/")
def root():
    return {"message": "Rate My Resume API"}


@app.get("/health")
def health():
    return {"status": "ok"}


async def event_generator(resume_path, jd, user_id):
    """Generates progress events for resume analysis."""
    def send_event(stage, message):
        yield f"data: {json.dumps({'stage': stage, 'message': message})}\n\n"

    try:
        async for item in send_event("extraction", "Extracting resume content..."):
            yield item
        markdown = extract(resume_path)
        if len(markdown) < 50: raise ValueError("Could not extract meaningful text from file")
        
        async for item in send_event("parsing", "Parsing resume structure..."):
            yield item
        resume = extract_resume(markdown)
        
        async for item in send_event("analysis", "Analyzing resume content..."):
            yield item
        analysis = analyze_resume(resume, jd=jd)
        
        async for item in send_event("formatting", "Finalizing audit report..."):
            yield item
        result = transform_to_frontend_format(analysis, resume=resume)
        
        yield f"data: {json.dumps({'status': 'complete', 'result': result})}\n\n"
    except Exception as e:
        logger.error(f"Error in SSE stream: {e}")
        yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

@app.get("/api/analyze-stream")
async def analyze_resume_stream(file_path: str, jd: Optional[str] = None, user_id: Optional[str] = None):
    return StreamingResponse(event_generator(file_path, jd, user_id), media_type="text/event-stream")


@app.post("/api/analyze")
async def analyze_resume_endpoint(
    file: UploadFile = File(...),
    jd: Optional[str] = None,
    current_user: dict = Depends(verify_premium_user),
):
    user_id = current_user.get("id")
    
    if not file.filename.lower().endswith((".pdf", ".docx")): raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024: raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB")
    
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        async def process_resume_async():
            markdown = extract(tmp_path)
            if len(markdown) < 50: raise ValueError("Could not extract meaningful text from file")
            resume = extract_resume(markdown)
            analysis = await analyze_resume(resume, jd=jd)
            
            # Use run_in_threadpool only for the blocking transform/suggestion logic if needed, 
            # but transform_to_frontend_format seems fast enough to run directly or we can keep it in threadpool.
            # For now, let's just await the analysis and do the rest.
            from fastapi.concurrency import run_in_threadpool
            result = transform_to_frontend_format(analysis, resume=resume)
            
            actionable_suggestions = []
            for section in result.get('sections', []):
                if section['name'] in ('Experience', 'Projects'):
                    section_key = section['name'].lower()
                    for entry_idx, entry in enumerate(result.get(f'{section_key}_analysis', [])):
                        for bullet_idx, sug_item in enumerate(entry.get('suggestions', [])):
                            actionable_suggestions.append({"section": section_key, "entry_index": entry_idx, "bullet_index": bullet_idx, "bullet": sug_item.get("original_bullet", "") if isinstance(sug_item, dict) else str(sug_item), "advice": sug_item.get("advice", "") if isinstance(sug_item, dict) else str(sug_item)})
            
            if actionable_suggestions:
                from app.analyzer.batch_rewriter import batch_rewrite_suggestions
                rewrites = await batch_rewrite_suggestions(actionable_suggestions)
                for sug in actionable_suggestions:
                    section_key = sug['section']
                    entry_idx = sug['entry_index']
                    bullet_idx = sug['bullet_index']
                    entry_suggestions = result.get(f'{section_key}_analysis', [])[entry_idx].get('suggestions', [])
                    if isinstance(entry_suggestions[bullet_idx], dict): entry_suggestions[bullet_idx]["rewrites"] = rewrites.get(f"{section_key}__{entry_idx}__{bullet_idx}", [])
                    else: entry_suggestions[bullet_idx] = {"original_bullet": sug['bullet'], "advice": entry_suggestions[bullet_idx], "rewrites": rewrites.get(f"{section_key}__{entry_idx}__{bullet_idx}", [])}
            return result
        
        result = None
        for attempt in range(3):
            try:
                # Enforce a 60s timeout on the processing function
                result = await asyncio.wait_for(process_resume_async(), timeout=60.0)
                break
            except asyncio.TimeoutError:
                logger.warning(f"Analysis attempt {attempt + 1} timed out.")
                if attempt == 2:
                    raise HTTPException(status_code=504, detail="Analysis timed out after 3 attempts.")
            except Exception as e:
                logger.error(f"Analysis attempt {attempt + 1} failed: {e}")
                if attempt == 2:
                    raise HTTPException(status_code=500, detail=f"Analysis failed after 3 attempts: {str(e)}")
        
        if result is None:
            raise HTTPException(status_code=500, detail="Analysis failed.")
        
        if user_id:
            deduct_user_credit(user_id, f"Resume analysis: {file.filename}")
            
        analysis_id = None
        if user_id:
            try:
                from app.db import service_supabase
                insert_data = {"user_id": user_id, "file_name": file.filename, "result_json": result}
                db_response = service_supabase.table("analyses").insert(insert_data).execute()
                if db_response.data: analysis_id = db_response.data[0]["id"]
            except: pass
        
        return JSONResponse(content={"analysis_id": analysis_id, "analysis_data": result, "saved_to_history": bool(analysis_id)})
    
    finally:
        if tmp_path and os.path.exists(tmp_path): os.remove(tmp_path)


async def stream_analyze_generator(content: bytes, filename: str, jd: Optional[str], user_id: Optional[str], target_tier: Optional[str] = None):
    """Async generator for SSE streaming resume analysis."""
    def emit(stage: str, progress: int, message: str):
        return f"data: {json.dumps({'stage': stage, 'progress': progress, 'message': message})}\n\n"
    
    tmp_path = None
    try:
        # Validate file
        if not filename.lower().endswith((".pdf", ".docx")):
            yield emit("error", 0, "Only PDF and DOCX files are supported")
            return
        
        # Check size
        if len(content) > 10 * 1024 * 1024:
            yield emit("error", 0, "File too large. Maximum size is 10MB")
            return
        
        # Save to temp
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Check credits
        credits_before = 0
        if user_id:
            from app.dependencies import check_user_credits
            credits_before = check_user_credits(user_id)
            if credits_before < 1:
                yield emit("credits_error", 0, "Insufficient credits")
                return
        
        yield emit("extract", 5, "Extracting text from file...")
        
        from app.extractors import extract
        from app.llm import extract_resume
        
        markdown = extract(tmp_path)
        if len(markdown) < 50:
            yield emit("error", 0, "Could not extract meaningful text from file")
            return
        
        yield emit("parse", 15, "Parsing resume structure...")
        resume = extract_resume(markdown)
        
        yield emit("analyze_basic", 25, "Analyzing basic info...")
        yield emit("analyze_exp", 35, "Analyzing experience...")
        yield emit("analyze_projects", 45, "Analyzing projects...")
        yield emit("analyze_skills", 55, "Analyzing skills...")
        yield emit("analyze_education", 65, "Analyzing education...")
        yield emit("analyze_cert", 75, "Analyzing certifications...")
        
        analysis = await analyze_resume(resume, jd=jd)
        
        yield emit("format", 85, "Formatting results...")
        result = transform_to_frontend_format(analysis, resume=resume)
        
        # Process rewrites
        yield emit("rewrite", 92, "Generating improvement suggestions...")
        actionable_suggestions = []
        for section in result.get('sections', []):
            if section['name'] in ('Experience', 'Projects'):
                section_key = section['name'].lower()
                for entry_idx, entry in enumerate(result.get(f'{section_key}_analysis', [])):
                    for bullet_idx, sug_item in enumerate(entry.get('suggestions', [])):
                        actionable_suggestions.append({
                            "section": section_key,
                            "entry_index": entry_idx,
                            "bullet_index": bullet_idx,
                            "bullet": sug_item.get("original_bullet", "") if isinstance(sug_item, dict) else str(sug_item),
                            "advice": sug_item.get("advice", "") if isinstance(sug_item, dict) else str(sug_item)
                        })
        
        if actionable_suggestions:
            from app.analyzer.batch_rewriter import batch_rewrite_suggestions
            rewrites = await batch_rewrite_suggestions(actionable_suggestions)
            for sug in actionable_suggestions:
                section_key = sug['section']
                entry_idx = sug['entry_index']
                bullet_idx = sug['bullet_index']
                entry_suggestions = result.get(f'{section_key}_analysis', [])[entry_idx].get('suggestions', [])
                if isinstance(entry_suggestions[bullet_idx], dict):
                    entry_suggestions[bullet_idx]["rewrites"] = rewrites.get(f"{section_key}__{entry_idx}__{bullet_idx}", [])
                else:
                    entry_suggestions[bullet_idx] = {
                        "original_bullet": sug['bullet'],
                        "advice": entry_suggestions[bullet_idx],
                        "rewrites": rewrites.get(f"{section_key}__{entry_idx}__{bullet_idx}", [])
                    }
        
        # Deduct credits
        if user_id:
            from app.dependencies import deduct_user_credit
            deduct_user_credit(user_id, f"Resume analysis: {filename}")
        
        # Save to history
        analysis_id = None
        if user_id:
            try:
                from app.db import service_supabase
                insert_data = {"user_id": user_id, "file_name": filename, "result_json": result}
                db_response = service_supabase.table("analyses").insert(insert_data).execute()
                if db_response.data:
                    analysis_id = db_response.data[0]["id"]
            except:
                pass
        
        yield emit("complete", 100, "Analysis complete!")
        yield f"data: {json.dumps({'status': 'complete', 'result': result, 'analysis_id': analysis_id, 'saved_to_history': bool(analysis_id), 'credits_remaining': credits_before - 1})}\n\n"
    
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"SSE stream error: {e}\n{tb}")
        yield emit("error", 0, str(e))
        yield f"data: {json.dumps({'status': 'error', 'message': str(e), 'traceback': tb})}\n\n"
    
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/api/analyze/stream")
async def analyze_resume_stream_endpoint(
    file: UploadFile = File(...),
    jd: Optional[str] = None,
    target_tier: Optional[str] = None,
    current_user: dict = Depends(verify_premium_user),
):
    user_id = current_user.get("id")
    
    # Read file content here while the file is still open
    content = await file.read()
    
    return StreamingResponse(
        stream_analyze_generator(content, file.filename, jd, user_id, target_tier),
        media_type="text/event-stream"
    )


class RewriteRequest(BaseModel):
    bullet: str
    suggestion: str
    target_tier: Optional[str] = None


@app.post("/api/rewrite")
async def rewrite_bullet_endpoint(
    request: RewriteRequest,
    current_user: dict = Depends(get_current_user),
):
    from .analyzer.rewriter import rewrite_bullet
    from fastapi.concurrency import run_in_threadpool
    # target_tier is accepted but not currently used by the rewriter
    return await run_in_threadpool(lambda: rewrite_bullet(request.bullet, request.suggestion))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
