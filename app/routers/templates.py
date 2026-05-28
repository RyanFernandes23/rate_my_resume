from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO
from docx import Document
from ..template_service import list_templates

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("")
async def get_templates():
    return list_templates()


@router.get("/{template_id}/preview")
async def preview_template(template_id: str):
    templates = list_templates()
    if not any(t["id"] == template_id for t in templates):
        raise HTTPException(status_code=404, detail="Template not found")
    return {"template_id": template_id, "preview": "Dummy preview data"}


@router.get("/{template_id}/download")
async def download_template(template_id: str):
    templates = list_templates()
    template = next((t for t in templates if t["id"] == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    doc = Document()
    doc.add_heading(template["name"], level=0)
    doc.add_paragraph("This resume was built with RateMyResume.")
    doc.add_heading("Experience", level=1)
    doc.add_paragraph("Your experience entries will appear here.")
    doc.add_heading("Education", level=1)
    doc.add_paragraph("Your education details will appear here.")
    doc.add_heading("Skills", level=1)
    doc.add_paragraph("Your skills will appear here.")

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={template_id}.docx"},
    )
