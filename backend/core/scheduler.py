"""
APScheduler-based recurring audit scheduler.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import AsyncSessionLocal
from backend.db.models import AuditRecord, ScheduledAuditRecord
from backend.models.audit import AuditCreateRequest, TargetConfig
from backend.utils.config import settings

logger = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler()


# ── Internal job runner ───────────────────────────────────────────────────────

async def _run_scheduled_audit(scheduled_id: str) -> None:
    """Triggered by APScheduler. Creates and starts an audit from a ScheduledAuditRecord."""
    # Import here to avoid circular imports
    from backend.core.scanner import AuditOrchestrator
    from backend.core.risk_scorer import calculate_risk_score, get_risk_level, generate_executive_summary

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ScheduledAuditRecord).where(ScheduledAuditRecord.id == scheduled_id)
        )
        sched = result.scalar_one_or_none()
        if not sched or not sched.is_active:
            return

        try:
            target_cfg = TargetConfig(**sched.target_config)
            request = AuditCreateRequest(
                company_name=sched.company_name,
                target=target_cfg,
                scan_categories=sched.scan_categories,
            )

            # Create audit record
            audit = AuditRecord(
                company_name=request.company_name,
                target_url=str(request.target.url),
                target_provider=request.target.provider,
                target_model=request.target.model,
                system_prompt_hint=request.target.system_prompt_hint,
                status="running",
                reviewer_name=settings.REVIEWER_NAME,
            )
            session.add(audit)
            await session.flush()
            audit_id = audit.id

            sched.last_run_at = datetime.now(timezone.utc)
            await session.commit()

            logger.info("Starting scheduled audit %s for %s", audit_id, sched.company_name)

            orchestrator = AuditOrchestrator(audit_id, request)
            findings = await orchestrator.run(session)

            risk_score = calculate_risk_score(findings)
            risk_level = get_risk_level(risk_score)
            summary = generate_executive_summary(findings, risk_score, risk_level)

            result2 = await session.execute(
                select(AuditRecord).where(AuditRecord.id == audit_id)
            )
            audit_rec = result2.scalar_one()
            audit_rec.status = "completed"
            audit_rec.risk_score = risk_score
            audit_rec.risk_level = risk_level
            audit_rec.summary = summary
            audit_rec.completed_at = datetime.now(timezone.utc)
            await session.commit()

            logger.info("Scheduled audit %s complete — risk: %s (%.1f)", audit_id, risk_level, risk_score)

        except Exception as exc:
            logger.error("Scheduled audit failed for %s: %s", scheduled_id, exc)


# ── Public API ────────────────────────────────────────────────────────────────

def start_scheduler() -> None:
    if not _scheduler.running:
        _scheduler.start()
        logger.info("APScheduler started")


def stop_scheduler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")


def schedule_audit(scheduled_id: str, cron_expression: str) -> None:
    """Add or replace a cron job for the given ScheduledAuditRecord."""
    job_id = f"scheduled_audit_{scheduled_id}"
    if _scheduler.get_job(job_id):
        _scheduler.remove_job(job_id)

    parts = cron_expression.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression: {cron_expression!r}")

    minute, hour, day, month, day_of_week = parts
    trigger = CronTrigger(
        minute=minute, hour=hour, day=day,
        month=month, day_of_week=day_of_week
    )
    _scheduler.add_job(
        _run_scheduled_audit,
        trigger=trigger,
        args=[scheduled_id],
        id=job_id,
        replace_existing=True,
    )
    logger.info("Scheduled audit job registered: %s (%s)", job_id, cron_expression)


def remove_scheduled_audit(scheduled_id: str) -> None:
    job_id = f"scheduled_audit_{scheduled_id}"
    if _scheduler.get_job(job_id):
        _scheduler.remove_job(job_id)
        logger.info("Removed scheduled job: %s", job_id)


async def load_all_schedules(session: AsyncSession) -> None:
    """Re-register all active scheduled audits from the database on startup."""
    result = await session.execute(
        select(ScheduledAuditRecord).where(ScheduledAuditRecord.is_active == True)
    )
    schedules = result.scalars().all()
    for sched in schedules:
        try:
            schedule_audit(sched.id, sched.cron_expression)
        except Exception as exc:
            logger.warning("Failed to load schedule %s: %s", sched.id, exc)
    logger.info("Loaded %d scheduled audits from database", len(schedules))
