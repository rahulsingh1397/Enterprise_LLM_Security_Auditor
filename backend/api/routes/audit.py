"""
Audit API routes.
"""

import asyncio
import json
import uuid
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.scanner import AuditOrchestrator
from db.database import AsyncSessionLocal, get_db
from db import models as db_models
from models.audit import AuditBrief, AuditCreateRequest, AuditDetail, ProgressEvent
from models.vulnerability import FindingOut
from utils.config import settings
from utils.logger import get_logger

router = APIRouter(prefix="/audits", tags=["audits"])
logger = get_logger(__name__)

# In-memory registry of active WebSocket connections per audit
_ws_connections: dict[str, list[WebSocket]] = {}


async def _broadcast(audit_id: str, event: ProgressEvent):
    """Send progress events to all WebSocket clients watching this audit."""
    connections = _ws_connections.get(audit_id, [])
    dead = []
    for ws in connections:
        try:
            await ws.send_text(event.model_dump_json())
        except Exception:
            dead.append(ws)
    for ws in dead:
        connections.remove(ws)


async def _run_audit_background(audit_id: str, request: AuditCreateRequest):
    """Background task that runs the full audit."""
    async with AsyncSessionLocal() as db:
        orchestrator = AuditOrchestrator(db)

        async def _callback(event: ProgressEvent):
            await _broadcast(audit_id, event)

        await orchestrator.run(audit_id, request, progress_callback=_callback)


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("", response_model=AuditBrief, status_code=202)
async def create_audit(
    request: AuditCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create a new audit and start it in the background."""
    audit_id = str(uuid.uuid4())

    record = db_models.AuditRecord(
        id=audit_id,
        company_name=request.company_name,
        target_url=request.target.url or f"https://api.{request.target.provider}.com",
        target_provider=request.target.provider,
        target_model=request.target.model,
        system_prompt_hint=request.target.system_prompt_hint,
        status="pending",
        reviewer_name=settings.REVIEWER_NAME,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    _ws_connections[audit_id] = []
    background_tasks.add_task(_run_audit_background, audit_id, request)

    return record


@router.get("", response_model=List[AuditBrief])
async def list_audits(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(db_models.AuditRecord)
        .order_by(db_models.AuditRecord.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{audit_id}", response_model=AuditDetail)
async def get_audit(audit_id: str, db: AsyncSession = Depends(get_db)):
    record = await db.get(db_models.AuditRecord, audit_id)
    if not record:
        raise HTTPException(status_code=404, detail="Audit not found")
    return record


@router.get("/{audit_id}/findings", response_model=List[FindingOut])
async def get_findings(
    audit_id: str,
    vulnerable_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    query = select(db_models.FindingRecord).where(
        db_models.FindingRecord.audit_id == audit_id
    )
    if vulnerable_only:
        query = query.where(db_models.FindingRecord.vulnerable == True)  # noqa: E712
    result = await db.execute(query)
    return result.scalars().all()


@router.delete("/{audit_id}", status_code=204)
async def delete_audit(audit_id: str, db: AsyncSession = Depends(get_db)):
    record = await db.get(db_models.AuditRecord, audit_id)
    if not record:
        raise HTTPException(status_code=404, detail="Audit not found")

    # Delete findings
    from sqlalchemy import delete as sql_delete
    await db.execute(
        sql_delete(db_models.FindingRecord).where(
            db_models.FindingRecord.audit_id == audit_id
        )
    )
    await db.delete(record)
    await db.commit()


# ── WebSocket ─────────────────────────────────────────────────────────────────

@router.websocket("/{audit_id}/progress")
async def audit_progress_ws(audit_id: str, websocket: WebSocket):
    """Real-time progress stream for a running audit."""
    await websocket.accept()

    if audit_id not in _ws_connections:
        _ws_connections[audit_id] = []
    _ws_connections[audit_id].append(websocket)

    logger.info("WS client connected for audit %s", audit_id)

    try:
        while True:
            # Keep alive — wait for client ping or disconnect
            data = await asyncio.wait_for(websocket.receive_text(), timeout=60)
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    finally:
        conns = _ws_connections.get(audit_id, [])
        if websocket in conns:
            conns.remove(websocket)
        logger.info("WS client disconnected from audit %s", audit_id)
