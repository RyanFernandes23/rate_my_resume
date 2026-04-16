import logging
import os

logger = logging.getLogger(__name__)


class ResumeExtractor:
    def __init__(self):
        self._converter = None
        self._docling_import_error = None
        logger.info("ResumeExtractor initialized")

    def _get_converter(self):
        if self._converter is not None:
            return self._converter

        if self._docling_import_error is not None:
            raise RuntimeError(self._docling_import_error)

        try:
            from docling.document_converter import DocumentConverter

            self._converter = DocumentConverter()
            return self._converter
        except Exception as exc:
            self._docling_import_error = (
                "Docling could not be initialized. "
                "The current environment fails while importing Torch, which Docling depends on. "
                f"Original error: {exc}"
            )
            logger.exception("Failed to initialize Docling")
            raise RuntimeError(self._docling_import_error) from exc

    def extract(self, file_path: str) -> str:
        _, ext = os.path.splitext(file_path.lower())

        if ext not in {".pdf", ".docx", ".doc"}:
            raise ValueError(f"Unsupported file type: {ext}")

        logger.info("Extracting document with Docling: %s", file_path)

        converter = self._get_converter()
        result = converter.convert(file_path)
        text_content = result.document.export_to_markdown().strip()

        if not text_content:
            raise ValueError("No content extracted from document")

        logger.info("Extracted %s chars from document", len(text_content))
        return text_content
