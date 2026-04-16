from .pdf import extract_pdf
from .docx import extract_docx


def extract(file_path: str) -> str:
    ext = file_path.lower().split(".")[-1]

    if ext == "pdf":
        return extract_pdf(file_path)
    elif ext == "docx":
        return extract_docx(file_path)
    else:
        raise ValueError(f"Unsupported format: .{ext}")
