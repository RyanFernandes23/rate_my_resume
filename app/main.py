from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional
import os
import json
import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

from app.db import settings, service_supabase
from app.llm import create_llm_client
from app.repositories.credit import SupabaseCreditRepository
from app.repositories.analysis import SupabaseAnalysisRepository
from app.pipeline import AnalysisPipeline, PipelineContext, ProgressEvent, PipelineResult
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.rate_limit import limiter
from app.routers import auth, credits, payments, history
from app.dependencies import verify_premium_user, get_optional_user
from app.routers.auth import get_current_user

app = FastAPI(title="Rate My Resume API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

app.include_router(auth.router)
app.include_router(credits.router)
app.include_router(payments.router)
app.include_router(history.router)


@app.middleware("http")
async def enforce_https(request: Request, call_next):
    forwarded_proto = request.headers.get("X-Forwarded-Proto")
    if forwarded_proto and forwarded_proto == "http":
        return JSONResponse(
            status_code=403,
            content={"detail": "HTTPS required"},
        )
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)


def _validate_resume_file(file: UploadFile, content: bytes) -> None:
    allowed_extensions = (".pdf", ".docx")
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB")

    if file.filename.lower().endswith(".pdf") and not content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Invalid PDF file")
    if file.filename.lower().endswith(".docx") and not content.startswith(b"PK"):
        raise HTTPException(status_code=400, detail="Invalid DOCX file")


def _validate_jd(jd: Optional[str]) -> None:
    if jd and len(jd) > 5000:
        raise HTTPException(
            status_code=400, detail="Job description exceeds maximum length of 5000 characters"
        )


def get_pipeline() -> AnalysisPipeline:
    slow_client = create_llm_client()
    fast_client = create_llm_client(model="llama-3.1-8b-instant")
    credit_repo = SupabaseCreditRepository(service_supabase)
    analysis_repo = SupabaseAnalysisRepository(service_supabase)
    return AnalysisPipeline(slow_client, credit_repo, analysis_repo, fast_llm_client=fast_client)


@app.get("/")
def root():
    return {"message": "Rate My Resume API"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/analyze-stream")
async def analyze_resume_stream(
    file_path: str,
    jd: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """Legacy SSE endpoint. Prefer POST /api/analyze/stream."""
    with open(file_path, "rb") as f:
        content = f.read()
    filename = os.path.basename(file_path)
    ctx = PipelineContext(file_content=content, filename=filename, jd=jd, user_id=user_id)
    pipeline = get_pipeline()

    async def generate():
        async for event in pipeline.run(ctx):
            if isinstance(event, ProgressEvent):
                yield f"data: {json.dumps({'stage': event.stage, 'message': event.message})}\n\n"
                if event.stage == "error":
                    yield f"data: {json.dumps({'status': 'error', 'message': event.message})}\n\n"
            elif isinstance(event, PipelineResult):
                yield f"data: {json.dumps({'status': 'complete', 'result': event.analysis_data})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/analyze")
async def analyze_resume_endpoint(
    file: UploadFile = File(...),
    jd: Optional[str] = None,
    current_user: dict = Depends(verify_premium_user),
):
    user_id = current_user.get("id")
    _validate_jd(jd)
    content = await file.read()
    _validate_resume_file(file, content)

    ctx = PipelineContext(
        file_content=content,
        filename=file.filename,
        jd=jd,
        user_id=user_id,
    )
    pipeline = get_pipeline()

    try:
        result = await asyncio.wait_for(
            _collect_sync_result(pipeline, ctx), timeout=90.0
        )
        if result is None:
            raise HTTPException(status_code=500, detail="Analysis failed.")
        return JSONResponse(
            content={
                "analysis_id": result.analysis_id,
                "analysis_data": result.analysis_data,
                "saved_to_history": result.saved_to_history,
            }
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Analysis timed out. The resume is too complex or the AI is overloaded. Please use the streaming endpoint instead.",
        )


async def _collect_sync_result(
    pipeline: AnalysisPipeline, ctx: PipelineContext
) -> Optional[PipelineResult]:
    async for event in pipeline.run(ctx):
        if isinstance(event, ProgressEvent):
            if event.stage == "error":
                raise HTTPException(status_code=400, detail=event.message)
            if event.stage == "credits_error":
                raise HTTPException(status_code=402, detail=event.message)
        elif isinstance(event, PipelineResult):
            return event
    return None


@app.post("/api/analyze/stream")
async def analyze_resume_stream_endpoint(
    file: UploadFile = File(...),
    jd: Optional[str] = None,
    current_user: dict = Depends(verify_premium_user),
):
    user_id = current_user.get("id")
    _validate_jd(jd)
    content = await file.read()
    _validate_resume_file(file, content)

    ctx = PipelineContext(
        file_content=content,
        filename=file.filename,
        jd=jd,
        user_id=user_id,
    )
    pipeline = get_pipeline()

    async def generate():
        async for event in pipeline.run(ctx):
            if isinstance(event, ProgressEvent):
                yield f"data: {json.dumps({'stage': event.stage, 'progress': event.progress, 'message': event.message})}\n\n"
                if event.stage in ("error", "credits_error"):
                    yield f"data: {json.dumps({'status': 'error', 'message': event.message})}\n\n"
            elif isinstance(event, PipelineResult):
                yield f"data: {json.dumps({'status': 'complete', 'result': event.analysis_data, 'analysis_id': event.analysis_id, 'saved_to_history': event.saved_to_history, 'credits_remaining': event.credits_remaining})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


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

    llm_client = create_llm_client()
    result = await rewrite_bullet(request.bullet, request.suggestion, llm_client)
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
