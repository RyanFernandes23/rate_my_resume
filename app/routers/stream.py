"""WebSocket stream endpoint for non-blocking resume analysis.
Currently not wired into main.py. Uses AnalysisPipeline when activated."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import Optional
import os
import logging

from app.pipeline import AnalysisPipeline, PipelineContext, ProgressEvent, PipelineResult
from app.llm import create_llm_client
from app.repositories.credit import SupabaseCreditRepository
from app.repositories.analysis import SupabaseAnalysisRepository
from app.db import service_supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["stream"])


def _get_pipeline() -> AnalysisPipeline:
    return AnalysisPipeline(
        create_llm_client(),
        SupabaseCreditRepository(service_supabase),
        SupabaseAnalysisRepository(service_supabase),
    )


@router.get("/api/stream/init")
async def initiate_stream():
    """Returns a placeholder. WebSocket streaming not yet active."""
    return JSONResponse({"job_id": None, "message": "Use POST /api/analyze/stream instead"})


@router.websocket("/ws/{job_id}")
async def websocket_stream(websocket: WebSocket, job_id: str):
    await websocket.close(code=4004, reason="WebSocket streaming not yet active")
