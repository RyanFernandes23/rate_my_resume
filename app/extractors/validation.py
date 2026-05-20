import pymupdf
import pymupdf4llm
import tempfile
import os

MAX_PAGES = 2


def get_page_count(file_path: str) -> tuple[int, str | None]:
    ext = file_path.lower().split(".")[-1]

    if ext == "pdf":
        doc = pymupdf.open(file_path)
        count = len(doc)
        doc.close()
        return count, None

    elif ext == "docx":
        import docx2pdf

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name

        docx2pdf.convert(file_path, tmp_path)
        doc = pymupdf.open(tmp_path)
        count = len(doc)
        doc.close()

        return count, tmp_path

    raise ValueError(f"Unsupported format: .{ext}")


def extract_pdf(file_path: str) -> str:
    return pymupdf4llm.to_markdown(file_path)


class ResumeTooLongError(Exception):
    """Custom exception for resume length validation."""
    def __init__(self, pages, max_pages):
        self.pages = pages
        self.max_pages = max_pages
        super().__init__(f"Resume exceeds {max_pages} pages ({pages} pages)")

def validate_pages(file_path: str) -> str | None:
    pages, pdf_path = get_page_count(file_path)
    if pages > MAX_PAGES:
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except PermissionError:
                pass
        raise ResumeTooLongError(pages, MAX_PAGES)
    return pdf_path


def cleanup_temp_pdf(pdf_path: str) -> None:
    if pdf_path and os.path.exists(pdf_path):
        try:
            os.remove(pdf_path)
        except PermissionError:
            pass
