"""
Report generation API routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db import models as db_models
from reports.generator import generate_html_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{audit_id}/html", response_class=HTMLResponse)
async def get_html_report(audit_id: str, db: AsyncSession = Depends(get_db)):
    """Return a fully rendered HTML audit report."""
    audit = await db.get(db_models.AuditRecord, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    if audit.status not in ("completed", "failed"):
        raise HTTPException(status_code=409, detail="Audit is not complete yet")

    result = await db.execute(
        select(db_models.FindingRecord).where(
            db_models.FindingRecord.audit_id == audit_id
        )
    )
    findings = result.scalars().all()

    html = generate_html_report(audit, findings)
    return HTMLResponse(content=html)
