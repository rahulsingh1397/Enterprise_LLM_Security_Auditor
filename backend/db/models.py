"""
SQLAlchemy ORM models.
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text, func
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
