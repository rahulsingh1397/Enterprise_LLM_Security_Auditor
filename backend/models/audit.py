"""
Pydantic schemas for audit requests / responses.
"""

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field, HttpUrl


# ── Request schemas ────────────────────────────────────────────────────────────

class TargetConfig(BaseModel):
    """Configuration for the LLM being audited."""
    provider: str = Field(..., description="openai | anthropic | custom")
    url: Optional[str] = Field(None, description="Base URL (required for custom provider)")
    api_key: str = Field(..., description="API key for target LLM")
    model: str = Field(..., description="Model name / ID")
    system_prompt_hint: Optional[str] = Field(
        None,
        description="Optional known system prompt to aid analysis",
    )
    timeout_seconds: int = Field(30, ge=5, le=120)


class AuditCreateRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    target: TargetConfig
    scan_categories: List[str] = Field(
        default=[
            "prompt_injection",
            "system_prompt_leakage",
            "data_leakage",
            "jailbreak",
            "pii_exposure",
            "rag_security",
        ],
        description="Scanner categories to include",
    )


# ── Response schemas ───────────────────────────────────────────────────────────

class AuditBrief(BaseModel):
    id: str
    company_name: str
    status: str
    risk_score: Optional[float]
    risk_level: Optional[str]
    total_tests: int
    vulnerabilities_found: int
    created_at: datetime
    completed_at: Optional[datetime]
    reviewer_name: str

    class Config:
        from_attributes = True


class AuditDetail(AuditBrief):
    target_url: str
    target_provider: str
    target_model: str
    summary: Optional[str]
    error_message: Optional[str]


class ProgressEvent(BaseModel):
    audit_id: str
    event: str          # progress | completed | error
    completed: int
    total: int
    percent: float
    scanner: str
    message: str
    latest_finding: Optional[Any] = None
