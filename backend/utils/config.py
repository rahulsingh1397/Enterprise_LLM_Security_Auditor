"""
Application configuration — loaded from environment / .env file.
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "Enterprise LLM Security Auditor"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── Server ───────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Anthropic (used as analyzer / report engine) ─────────────────────────
    ANTHROPIC_API_KEY: str = Field(..., description="Anthropic API key for analysis")
    ANALYZER_MODEL: str = "claude-sonnet-4-6"
    FAST_ANALYZER_MODEL: str = "claude-haiku-4-5-20251001"

    # ── Optional: OpenAI-compatible targets ──────────────────────────────────
    OPENAI_API_KEY: Optional[str] = None

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./security_auditor.db"

    # ── Reports ──────────────────────────────────────────────────────────────
    REPORTS_DIR: str = "./reports/output"

    # ── CORS ─────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # ── Audit metadata ───────────────────────────────────────────────────────
    REVIEWER_NAME: str = "Rahul Singh"

    # ── Scanner settings ─────────────────────────────────────────────────────
    SCAN_TIMEOUT_SECONDS: int = 30
    MAX_CONCURRENT_ATTACKS: int = 5
    ANALYZER_TEMPERATURE: float = 0.1

    # ── JWT Auth ─────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440   # 24h
    AUTH_ENABLED: bool = False   # Set True to require login

    # ── Email notifications ──────────────────────────────────────────────────
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "auditor@llmsecurity.ai"
    NOTIFY_ON_CRITICAL: bool = True

    # ── Dynamic attack generation ────────────────────────────────────────────
    DYNAMIC_ATTACKS_ENABLED: bool = False   # Uses extra Claude API calls
    DYNAMIC_ATTACKS_PER_SCAN: int = 5

    # ── Encryption key for sensitive DB fields ───────────────────────────────
    FIELD_ENCRYPTION_KEY: Optional[str] = None   # Fernet key (base64)

    # ── Tier / Rate limiting ─────────────────────────────────────────────────
    FREE_TIER_AUDITS_PER_MONTH: int = 5
    TIER_ENFORCEMENT: bool = False


settings = Settings()
