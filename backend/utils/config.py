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


settings = Settings()
