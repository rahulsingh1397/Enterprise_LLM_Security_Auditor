"""
Enterprise LLM Security Auditor — FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import audit, health, reports
from api.routes import auth as auth_routes
from api.routes import export as export_routes
from api.routes import templates as template_routes
from core.scheduler import load_all_schedules, start_scheduler, stop_scheduler
from db.database import AsyncSessionLocal, init_db
from utils.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    await init_db()
    logger.info("Database initialised")

    start_scheduler()
    async with AsyncSessionLocal() as session:
        await load_all_schedules(session)

    yield

    stop_scheduler()
    logger.info("Shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Automated red-team security auditing for LLM applications. "
        "Detects prompt injection, jailbreaks, data leakage, PII exposure, "
        "system prompt leakage, and RAG vulnerabilities."
    ),
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(auth_routes.router)
app.include_router(export_routes.router)
app.include_router(template_routes.router)


@app.get("/api")
async def api_root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
    }
