"""WebSocket stream endpoint for non-blocking resume analysis."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, Query
from fastapi.responses import JSONResponse
from starlette.status import WS_1001_GOING_AWAY
from typing import Optional
import tempfile, os, logging, json, traceback

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["stream"])

from app.stream_manager import get_stream_manager, StreamManager
from app.extractors import extract
from app.llm import extract_resume
from app.analyzer import analyze_resume
from app.dependencies import get_optional_user
from app.utils import transform_to_frontend_format

ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]


def _run_analysis_sync(job_id: str, content: bytes, filename: str, jd: Optional[str], user_id: Optional[str], target_tier: Optional[str] = None) -> None:
    """Runs full resume analysis in a background thread, emitting events via stream_managers job queue."""
    mgr = get_stream_manager()
    job = mgr.get_job(job_id)
    if not job:
        return

    try:
        tmp_path = None
        try:
            if not filename.lower().endswith((".pdf", ".docx")):
                job.error("Only PDF and DOCX files are supported")
                return

            if len(content) > 10 * 1024 * 1024:
                job.error("File too large. Maximum size is 10MB")
                return

            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name

            credits_before = 0
            if user_id:
                from app.dependencies import check_user_credits
                credits_before = check_user_credits(user_id)
                if credits_before < 1:
                    job.emit("credits_error", 0, "Insufficient credits")
                    mgr.broadcast(job_id, {"stage": "credits_error", "progress": 0, "message": "Insufficient credits", "status": "credits_error"})
                    return

            job.emit("extract", 5, "Extracting text from file...")
            mgr.broadcast(job_id, {"stage": "extract", "progress": 5, "message": "Extracting text from file..."})

            markdown = extract(tmp_path)
            if len(markdown) < 50:
                job.emit("error", 0, "Could not extract meaningful text from file")
                mgr.broadcast(job_id, {"stage": "error", "progress": 0, "message": "Could not extract meaningful text from file", "status": "error"})
                return

            job.emit("parse", 15, "Parsing resume structure...")
            mgr.broadcast(job_id, {"stage": "parse", "progress": 15, "message": "Parsing resume structure..."})
            resume = extract_resume(markdown)

            job.emit("analyze_basic", 25, "Analyzing basic info...")
            mgr.broadcast(job_id, {"stage": "analyze_basic", "progress": 25, "message": "Analyzing basic info..."})
            job.emit("analyze_exp", 35, "Analyzing experience...")
            mgr.broadcast(job_id, {"stage": "analyze_exp", "progress": 35, "message": "Analyzing experience..."})
            job.emit("analyze_projects", 45, "Analyzing projects...")
            mgr.broadcast(job_id, {"stage": "analyze_projects", "progress": 45, "message": "Analyzing projects..."})
            job.emit("analyze_skills", 55, "Analyzing skills...")
            mgr.broadcast(job_id, {"stage": "analyze_skills", "progress": 55, "message": "Analyzing skills..."})
            job.emit("analyze_education", 65, "Analyzing education...")
            mgr.broadcast(job_id, {"stage": "analyze_education", "progress": 65, "message": "Analyzing education..."})
            job.emit("analyze_cert", 75, "Analyzing certifications...")
            mgr.broadcast(job_id, {"stage": "analyze_cert", "progress": 75, "message": "Analyzing certifications..."})

            analysis = analyze_resume(resume, jd=jd)

            job.emit("format", 85, "Formatting results...")
            mgr.broadcast(job_id, {"stage": "format", "progress": 85, "message": "Formatting results..."})
            result = transform_to_frontend_format(analysis, resume=resume)

            job.emit("rewrite", 92, "Generating improvement suggestions...")
            mgr.broadcast(job_id, {"stage": "rewrite", "progress": 92, "message": "Generating improvement suggestions..."})
            actionable_suggestions = []
            for section in result.get("sections", []):
                if section["name"] in ("Experience", "Projects"):
                    section_key = section["name"].lower()
                    entries = result.get(f"{section_key}_analysis", [])
                    for entry_idx, entry in enumerate(entries):
                        for bullet_idx, sug_item in enumerate(entry.get("suggestions", [])):
                            if isinstance(sug_item, dict):
                                actionable_suggestions.append({
                                    "section": section_key,
                                    "entry_index": entry_idx,
                                    "bullet_index": bullet_idx,
                                    "bullet": sug_item.get("original_bullet", ""),
                                    "advice": sug_item.get("advice", ""),
                                })
                            else:
                                actionable_suggestions.append({
                                    "section": section_key,
                                    "entry_index": entry_idx,
                                    "bullet_index": bullet_idx,
                                    "bullet": str(sug_item),
                                    "advice": "",
                                })

            if actionable_suggestions:
                from app.analyzer.batch_rewriter import batch_rewrite_suggestions
                rewrites = batch_rewrite_suggestions(actionable_suggestions)
                for sug in actionable_suggestions:
                    section_key = sug["section"]
                    entry_idx = sug["entry_index"]
                    bullet_idx = sug["bullet_index"]
                    entry_suggestions = result.get(f"{section_key}_analysis", [])[entry_idx].get("suggestions", [])
                    if isinstance(entry_suggestions[bullet_idx], dict):
                        entry_suggestions[bullet_idx]["rewrites"] = rewrites.get(f"{section_key}__{entry_idx}__{bullet_idx}", [])
                    else:
                        entry_suggestions[bullet_idx] = {
                            "original_bullet": sug["bullet"],
                            "advice": entry_suggestions[bullet_idx],
                            "rewrites": rewrites.get(f"{section_key}__{entry_idx}__{bullet_idx}", []),
                        }

            if user_id:
                from app.dependencies import deduct_user_credit
                deduct_user_credit(user_id, f"Resume analysis: {filename}")

            analysis_id = None
            if user_id:
                try:
                    from app.db import service_supabase
                    insert_data = {"user_id": user_id, "file_name": filename, "result_json": result}
                    db_response = service_supabase.table("analyses").insert(insert_data).execute()
                    if db_response.data:
                        analysis_id = db_response.data[0]["id"]
                except Exception as e:
                    logger.error(f"Failed to save to history: {e}")

            job.emit("complete", 100, "Analysis complete!")
            complete_event = {
                "stage": "complete",
                "progress": 100,
                "message": "Analysis complete!",
                "status": "complete",
                "result": result,
                "analysis_id": analysis_id,
                "saved_to_history": bool(analysis_id),
                "credits_remaining": credits_before - 1,
            }
            job.complete(result)
            mgr.broadcast(job_id, complete_event)

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Background job error: {e}\n{tb}")
        if job:
            job.error(str(e))
            mgr.broadcast(job_id, {"stage": "error", "progress": 0, "message": str(e), "status": "error", "traceback": tb})


@router.get("/api/stream/init")
async def initiate_stream(
    current_user: Optional[dict] = None,
):
    """Create a stream job and return the job_id. The WebSocket connects to /ws/{job_id}."""
    mgr = get_stream_manager()
    job_id = mgr.create_job()
    logger.info(f"Created stream job: {job_id}")
    return JSONResponse({"job_id": job_id})


@router.websocket("/ws/{job_id}")
async def websocket_stream(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for streaming progress. Client connects after receiving job_id."""
    mgr = get_stream_manager()

    if not mgr.get_job(job_id):
        await websocket.close(code=4004, reason="Job not found")
        return

    await websocket.accept()
    mgr.register_websocket(job_id, websocket)
    logger.info(f"WebSocket connected for job: {job_id}")

    try:
        while True:
            job = mgr.get_job(job_id)
            if not job:
                break

            event = job.get_event(timeout=0.5)
            if event:
                await websocket.send_json(event)
                if event.get("status") == "complete" or event.get("status") == "error":
                    break

            if job.is_done():
                if job.result is None:
                    break

    except Exception as e:
        logger.warning(f"WS read error for job {job_id}: {e}")
    finally:
        mgr.unregister_websocket(job_id, websocket)
        mgr.cleanup(job_id)
        logger.info(f"WebSocket disconnected for job: {job_id}")
        try:
            await websocket.close(code=WS_1001_GOING_AWAY)
        except Exception:
            pass