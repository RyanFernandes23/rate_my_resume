import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "action"):
            log_data["action"] = record.action
        if hasattr(record, "status"):
            log_data["status"] = record.status
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "model"):
            log_data["model"] = record.model
        if hasattr(record, "error"):
            log_data["error"] = record.error
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra

        return json.dumps(log_data)


def setup_logging(
    name: str = "rate_my_resume",
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()

    formatter = StructuredFormatter()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_api_call(
    action: str,
    status: str,
    duration_ms: int,
    model: Optional[str] = None,
    error: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    logger = logging.getLogger("rate_my_resume")
    log_record = logging.LogRecord(
        name="rate_my_resume",
        level=logging.INFO if status == "success" else logging.ERROR,
        pathname="",
        lineno=0,
        msg=f"{action} - {status}",
        args=(),
        exc_info=None,
    )
    log_record.action = action
    log_record.status = status
    log_record.duration_ms = duration_ms
    if model:
        log_record.model = model
    if error:
        log_record.error = error
    if extra:
        log_record.extra = extra

    logger.handle(log_record)
