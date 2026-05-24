import os

import pymupdf
import pymupdf4llm
from docx import Document

__all__ = ["extract", "ResumeTooLongError"]

MAX_PAGES = 4


class ResumeTooLongError(Exception):
    def __init__(self, pages: int, max_pages: int) -> None:
        self.pages = pages
        self.max_pages = max_pages
        super().__init__(f"Resume exceeds {max_pages} pages ({pages} pages)")


def _extract_pdf(file_path: str) -> str:
    doc = pymupdf.open(file_path)
    page_count = len(doc)
    doc.close()

    if page_count > MAX_PAGES:
        raise ResumeTooLongError(page_count, MAX_PAGES)

    return pymupdf4llm.to_markdown(file_path)


def _extract_docx(file_path: str) -> str:
    doc = Document(file_path)
    lines: list[str] = []

    for para in doc.paragraphs:
        if para.text.strip():
            lines.append(para.text)

    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            lines.append(" | ".join(cells))

    return "\n\n".join(lines)


def extract(file_path: str) -> str:
    ext = file_path.lower().rsplit(".", 1)[-1]

    if ext == "pdf":
        return _extract_pdf(file_path)

    if ext == "docx":
        return _extract_docx(file_path)

    raise ValueError(f"Unsupported format: .{ext}")
