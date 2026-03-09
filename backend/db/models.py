"""
SQLAlchemy ORM models.
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class AuditRecord(Base):
    __tablename__ = "audits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    company_name: Mapped[str] = mapped_column(String(255))
    target_url: Mapped[str] = mapped_column(String(500))
    target_provider: Mapped[str] = mapped_column(String(50))   # openai | anthropic | custom
    target_model: Mapped[str] = mapped_column(String(100))
    system_prompt_hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")  # pending|running|completed|failed
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    total_tests: Mapped[int] = mapped_column(Integer, default=0)
    tests_passed: Mapped[int] = mapped_column(Integer, default=0)   # tests where app is safe
    vulnerabilities_found: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewer_name: Mapped[str] = mapped_column(String(100), default="Rahul Singh")


class FindingRecord(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    audit_id: Mapped[str] = mapped_column(String(36), index=True)
    scanner_name: Mapped[str] = mapped_column(String(100))
    attack_name: Mapped[str] = mapped_column(String(200))
    attack_prompt: Mapped[str] = mapped_column(Text)
    target_response: Mapped[str] = mapped_column(Text)
    vulnerable: Mapped[bool] = mapped_column(default=False)
    severity: Mapped[str] = mapped_column(String(20))  # critical|high|medium|low|info
    confidence: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="analyst")  # admin|analyst|viewer
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100))   # audit_created|audit_deleted|report_viewed|login
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # audit|report|user
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ScheduledAuditRecord(Base):
    __tablename__ = "scheduled_audits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255))
    cron_expression: Mapped[str] = mapped_column(String(100))   # e.g. "0 9 * * 1"
    target_config: Mapped[dict] = mapped_column(JSON)           # TargetConfig dict
    scan_categories: Mapped[list] = mapped_column(JSON)
    company_name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
