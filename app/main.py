from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import time
import logging

from app.extractor import ResumeExtractor
from app.parser import ResumeParser
from app.feedback import FeedbackGenerator
from app.models import AnalysisResult
from app.logger import setup_logging, log_api_call

app = FastAPI(title="Rate My Resume API")

setup_logging(level=logging.INFO)
logger = logging.getLogger("rate_my_resume")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

extractor = ResumeExtractor()
parser = ResumeParser()
feedback_generator = FeedbackGenerator()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}


def allowed_file(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXTENSIONS


def count_pages(text_content: str) -> int:
    lines = text_content.split("\n")
    page_markers = sum(1 for line in lines if line.strip().startswith("## Page"))
    if page_markers > 0:
        return page_markers
    char_count = len(text_content)
    if char_count > 3000:
        return 3
    elif char_count > 1500:
        return 2
    return 1


@app.get("/")
def root():
    return {"message": "Rate My Resume API", "version": "1.0.0"}


@app.post("/api/analyze")
async def analyze_resume(file: UploadFile = File(...)) -> AnalysisResult:
    start_time = time.time()

    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    with tempfile.NamedTemporaryFile(
        delete=False, suffix=os.path.splitext(file.filename)[1]
    ) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name

    validation_errors = []

    try:
        logger.info(f"Starting analysis for file: {file.filename}")

        text_content = extractor.extract(tmp_file_path)
        page_count = count_pages(text_content)

        if page_count > 2:
            validation_errors.append(
                "Resume is longer than 2 pages. Consider condensing."
            )

        extracted_data = parser.parse(text_content)

        section_scores = feedback_generator.generate(extracted_data, page_count)
        base_score, bonus_score, total_score = (
            feedback_generator.calculate_final_scores(section_scores)
        )

        duration = int((time.time() - start_time) * 1000)
        log_api_call(
            "analyze_resume",
            "success",
            duration,
            extra={
                "page_count": page_count,
                "base_score": base_score,
                "bonus_score": bonus_score,
                "total_score": total_score,
            },
        )

        logger.info(f"Analysis completed in {duration}ms")

        return AnalysisResult(
            extracted_data=extracted_data,
            base_score=round(base_score, 2),
            bonus_score=round(bonus_score, 2),
            total_score=round(total_score, 2),
            section_scores=section_scores,
            page_count=page_count,
            is_valid=True,
            validation_errors=validation_errors,
        )

    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        log_api_call("analyze_resume", "error", duration, error=str(e))
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Resume analysis failed",
                "error": str(e),
                "validation_errors": validation_errors + [str(e)],
            },
        )

    finally:
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
