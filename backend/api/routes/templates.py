"""
Audit templates API — list and get pre-built audit configurations.
"""

from fastapi import APIRouter, HTTPException

from utils.templates import get_template, list_templates

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("/")
async def list_audit_templates():
    return list_templates()


@router.get("/{template_id}")
async def get_audit_template(template_id: str):
    template = get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template
