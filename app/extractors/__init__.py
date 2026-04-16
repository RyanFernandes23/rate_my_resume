from .validation import validate_pages, extract_pdf, cleanup_temp_pdf


def extract(file_path: str) -> str:
    pdf_path = validate_pages(file_path)

    ext = file_path.lower().split(".")[-1]

    if ext == "pdf":
        return extract_pdf(file_path)
    elif ext == "docx":
        if pdf_path:
            result = extract_pdf(pdf_path)
            cleanup_temp_pdf(pdf_path)
            return result
        raise ValueError("Failed to convert DOCX to PDF")
    else:
        raise ValueError(f"Unsupported format: .{ext}")
