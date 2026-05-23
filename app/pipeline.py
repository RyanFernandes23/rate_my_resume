"""Single AnalysisPipeline module — the only place the full analysis sequence lives."""
import os
import tempfile
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Optional

from .llm.protocol import LLMClient
from .llm import extract_resume
from .repositories.credit import CreditRepository
from .repositories.analysis import AnalysisRepository
from .extractors import extract as extract_text
from .analyzer import analyze_resume as run_analyzers
from .analyzer.batch_rewriter import batch_rewrite_suggestions
from .utils import transform_to_frontend_format

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 10 * 1024 * 1024
SUPPORTED_EXTENSIONS = (".pdf", ".docx")


@dataclass
class PipelineContext:
    file_content: bytes
    filename: str
    jd: Optional[str] = None
    user_id: Optional[str] = None


@dataclass
class ProgressEvent:
    stage: str
    progress: int
    message: str


@dataclass
class PipelineResult:
    analysis_data: dict
    analysis_id: Optional[str] = None
    saved_to_history: bool = False
    credits_remaining: Optional[int] = None


class AnalysisPipeline:
    def __init__(
        self,
        llm_client: LLMClient,
        credit_repo: CreditRepository,
        analysis_repo: AnalysisRepository,
    ) -> None:
        self._llm_client = llm_client
        self._credit_repo = credit_repo
        self._analysis_repo = analysis_repo

    async def run(
        self, ctx: PipelineContext
    ) -> AsyncIterator[ProgressEvent | PipelineResult]:
        tmp_path: Optional[str] = None
        credits_before = 0

        try:
            # --- Validation ---
            ext = os.path.splitext(ctx.filename)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                yield ProgressEvent("error", 0, "Only PDF and DOCX files are supported")
                return

            if len(ctx.file_content) > MAX_FILE_SIZE:
                yield ProgressEvent("error", 0, "File too large. Maximum size is 10MB")
                return

            # --- Temp file ---
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=ext
            ) as tmp_file:
                tmp_file.write(ctx.file_content)
                tmp_path = tmp_file.name

            # --- Credit check ---
            if ctx.user_id:
                credits_before = await self._credit_repo.get_balance(ctx.user_id)
                if credits_before < 1:
                    yield ProgressEvent(
                        "credits_error", 0, "Insufficient credits"
                    )
                    return

            yield ProgressEvent("extract", 5, "Extracting text from file...")
            markdown = extract_text(tmp_path)
            if len(markdown) < 50:
                yield ProgressEvent(
                    "error", 0, "Could not extract meaningful text from file"
                )
                return

            yield ProgressEvent("parse", 15, "Parsing resume structure...")
            resume = await extract_resume(markdown, self._llm_client)

            yield ProgressEvent("analyze_basic", 25, "Analyzing basic info...")
            yield ProgressEvent("analyze_exp", 35, "Analyzing experience...")
            yield ProgressEvent("analyze_projects", 45, "Analyzing projects...")
            yield ProgressEvent("analyze_skills", 55, "Analyzing skills...")
            yield ProgressEvent("analyze_education", 65, "Analyzing education...")
            yield ProgressEvent("analyze_cert", 75, "Analyzing certifications...")

            analysis = await run_analyzers(resume, self._llm_client, jd=ctx.jd)

            yield ProgressEvent("format", 85, "Formatting results...")
            result = transform_to_frontend_format(analysis, resume=resume)

            # --- Rewrites ---
            yield ProgressEvent("rewrite", 92, "Generating improvement suggestions...")
            await self._attach_rewrites(result)

            # --- Credit deduction ---
            if ctx.user_id:
                await self._credit_repo.deduct(
                    ctx.user_id, f"Resume analysis: {ctx.filename}"
                )

            # --- History ---
            analysis_id = None
            if ctx.user_id:
                analysis_id = await self._analysis_repo.save(
                    ctx.user_id, ctx.filename, result
                )

            credits_remaining = (
                credits_before - 1 if ctx.user_id else None
            )

            yield PipelineResult(
                analysis_data=result,
                analysis_id=analysis_id,
                saved_to_history=bool(analysis_id),
                credits_remaining=credits_remaining,
            )

        except Exception:
            import traceback

            tb = traceback.format_exc()
            logger.error(f"Pipeline error:\n{tb}")
            yield ProgressEvent("error", 0, "Analysis failed")

            # Refund credit on failure
            if ctx.user_id and credits_before > 0:
                await self._credit_repo.refund(ctx.user_id, "Analysis failed")

        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except PermissionError:
                    pass

    async def _attach_rewrites(self, result: dict) -> None:
        actionable_suggestions = []
        for section in result.get("sections", []):
            if section["name"] in ("Experience", "Projects"):
                section_key = section["name"].lower()
                entries = result.get(f"{section_key}_analysis", [])
                for entry_idx, entry in enumerate(entries):
                    for bullet_idx, sug_item in enumerate(
                        entry.get("suggestions", [])
                    ):
                        if isinstance(sug_item, dict):
                            actionable_suggestions.append(
                                {
                                    "section": section_key,
                                    "entry_index": entry_idx,
                                    "bullet_index": bullet_idx,
                                    "bullet": sug_item.get("original_bullet", ""),
                                    "advice": sug_item.get("advice", ""),
                                }
                            )
                        else:
                            actionable_suggestions.append(
                                {
                                    "section": section_key,
                                    "entry_index": entry_idx,
                                    "bullet_index": bullet_idx,
                                    "bullet": str(sug_item),
                                    "advice": "",
                                }
                            )

        if not actionable_suggestions:
            return

        rewrites = await batch_rewrite_suggestions(
            actionable_suggestions, self._llm_client
        )
        for sug in actionable_suggestions:
            section_key = sug["section"]
            entry_idx = sug["entry_index"]
            bullet_idx = sug["bullet_index"]
            entry_suggestions = (
                result.get(f"{section_key}_analysis", [])[entry_idx].get(
                    "suggestions", []
                )
            )
            key = f"{section_key}__{entry_idx}__{bullet_idx}"
            if isinstance(entry_suggestions[bullet_idx], dict):
                entry_suggestions[bullet_idx]["rewrites"] = rewrites.get(key, [])
            else:
                entry_suggestions[bullet_idx] = {
                    "original_bullet": sug["bullet"],
                    "advice": entry_suggestions[bullet_idx],
                    "rewrites": rewrites.get(key, []),
                }
