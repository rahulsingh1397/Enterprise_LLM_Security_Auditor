# Knowledge Transfer Document
## Enterprise LLM Security Auditor

**Author:** Rahul Singh
**Date:** March 2026
**Version:** 1.0
**Status:** Production Ready

---

## 1. Project Overview

### Purpose
Enterprise companies are deploying LLM-powered applications (chatbots, copilots, RAG systems) without security testing. This tool automates the red-teaming process — sending adversarial prompts to any LLM endpoint and using Claude to evaluate whether vulnerabilities were exposed.

### Business Value
- Security consultants can use this to offer LLM auditing services
- Internal security teams can integrate into CI/CD pipelines
- Average engagement: 61 tests in under 10 minutes vs. days of manual testing

### Revenue Model (if productized)
- SaaS: $500–$2,000/audit per company
- Consulting: $5,000–$15,000 for full engagement with report
- White-label: License to security firms

---

## 2. Architecture Decisions

### Why Claude as the Analyzer?
We use Claude (claude-haiku-4-5-20251001 for speed, claude-sonnet-4-6 for depth) as the analysis engine — not to send attacks, but to evaluate whether the target LLM's response reveals a vulnerability. This is the "analyzer" role. The target can be any LLM (OpenAI, Anthropic, custom).

**Alternative considered:** Rule-based regex matching — rejected because LLM responses are too varied and contextual. Claude understands nuance ("The AI refused but hinted at restricted topics" = partial vulnerability).

### Why SQLite?
Simple, zero-config, sufficient for single-instance deployments. Easy to back up (single file). Async via `aiosqlite`. Upgrade path to PostgreSQL: change `DATABASE_URL` in config — SQLAlchemy abstracts the rest.

### Why FastAPI + WebSockets for progress?
Audits take 2-10 minutes to run. WebSockets provide real-time progress without polling. The progress events stream directly from the background task to connected browser clients via an in-memory registry (`_ws_connections` dict in `audit.py`).

**Note:** The in-memory WS registry does not survive restarts or work across multiple server instances. For horizontal scaling, replace with Redis pub/sub.

### Why React + Vite (not Next.js)?
This is a pure SPA — no SSR needed. Vite gives faster dev experience and simpler build. The frontend proxies API calls to the backend, so no CORS issues in dev.

---

## 3. How the Scanner Works (Step-by-Step)

```
1. User submits AuditCreateRequest (company, target config, scan categories)
   ↓
2. FastAPI creates AuditRecord in SQLite (status: pending)
   ↓
3. BackgroundTask starts _run_audit_background(audit_id, request)
   ↓
4. AuditOrchestrator instantiates enabled scanners
   Each scanner exposes .attacks = [{name, prompt}]
   Total: up to 61 attack prompts
   ↓
5. asyncio.gather() runs all attacks concurrently (semaphore: 5 max)
   For each attack:
     a. TargetLLMClient.send(prompt) → response string
     b. ResponseAnalyzer.analyze(attack_type, name, prompt, response) → AnalysisResult
        (Uses Claude with strict JSON schema prompt)
     c. FindingRecord persisted to DB immediately
     d. ProgressEvent broadcast to WebSocket clients
   ↓
6. calculate_risk_score(all_findings) → 0-100 float
   (confidence-weighted, normalized to "10 criticals at 100%" worst case)
   ↓
7. AuditRecord updated: status=completed, risk_score, risk_level, summary
   ↓
8. Frontend WebSocket receives "completed" event, triggers data refresh
   ↓
9. User clicks "View Report" → GET /api/reports/{id}/html
   Jinja2 renders HTML from AuditRecord + FindingRecords
   Browser can Print → Save as PDF
```

---

## 4. File-by-File Reference

### Backend

| File | Purpose |
|---|---|
| `backend/main.py` | FastAPI app factory, lifespan, CORS, route registration |
| `backend/utils/config.py` | All settings via Pydantic BaseSettings (reads .env) |
| `backend/utils/logger.py` | Structured console logging |
| `backend/db/database.py` | Async engine, session factory, `init_db()` |
| `backend/db/models.py` | SQLAlchemy ORM: `AuditRecord`, `FindingRecord` |
| `backend/models/audit.py` | Pydantic: `AuditCreateRequest`, `TargetConfig`, `AuditBrief`, `ProgressEvent` |
| `backend/models/vulnerability.py` | Pydantic: `FindingCreate`, `FindingOut`, `AnalysisResult` |
| `backend/core/llm_client.py` | Sends attack prompts to target (OpenAI/Anthropic/custom) |
| `backend/core/analyzer.py` | Uses Claude to evaluate if attack succeeded → `AnalysisResult` |
| `backend/core/risk_scorer.py` | `calculate_risk_score()`, `get_risk_level()`, `generate_executive_summary()` |
| `backend/core/scanner.py` | `AuditOrchestrator.run()` — main coordination logic |
| `backend/scanners/base.py` | `BaseScanner` abstract class |
| `backend/scanners/prompt_injection.py` | 12 prompt injection attacks |
| `backend/scanners/system_prompt.py` | 10 system prompt leakage attacks |
| `backend/scanners/data_leakage.py` | 10 data extraction attacks |
| `backend/scanners/jailbreak.py` | 10 jailbreak attacks (DAN, developer mode, etc.) |
| `backend/scanners/pii_detection.py` | 9 PII exposure attacks |
| `backend/scanners/rag_security.py` | 10 RAG security attacks |
| `backend/api/routes/audit.py` | REST + WebSocket routes for audits |
| `backend/api/routes/reports.py` | HTML report endpoint |
| `backend/api/routes/health.py` | Health check |
| `backend/reports/generator.py` | Renders Jinja2 report template |
| `backend/reports/templates/report.html` | Professional audit report template |

### Frontend

| File | Purpose |
|---|---|
| `frontend/src/App.jsx` | Root component, sidebar nav, routing |
| `frontend/src/index.css` | Complete CSS design system (dark theme) |
| `frontend/src/services/api.js` | All API calls + WebSocket factory |
| `frontend/src/pages/Home.jsx` | Dashboard: stats, recent audits, feature overview |
| `frontend/src/pages/NewAudit.jsx` | 3-step wizard: target config → scan options → launch |
| `frontend/src/pages/AuditResults.jsx` | Real-time progress + tabbed results view |
| `frontend/src/pages/History.jsx` | Full audit history table with pagination |
| `frontend/src/components/RiskGauge.jsx` | SVG semi-circular gauge |
| `frontend/src/components/ScanProgress.jsx` | WebSocket-connected live scan log |
| `frontend/src/components/VulnerabilityCard.jsx` | Expandable vulnerability detail card |

---

## 5. Adding a New Scanner

1. Create `backend/scanners/my_scanner.py`:
```python
from backend.scanners.base import BaseScanner

class MyScanner(BaseScanner):
    name = "My Scanner"
    category = "my_category"

    @property
    def attacks(self):
        return [
            {"name": "Attack Name", "prompt": "The adversarial prompt text"},
        ]
```

2. Register in `backend/core/scanner.py`:
```python
from backend.scanners.my_scanner import MyScanner
_SCANNER_REGISTRY["my_category"] = MyScanner
```

3. Add to `SCAN_CATEGORIES` in `frontend/src/pages/NewAudit.jsx`.

That's it. The orchestrator handles everything else automatically.

---

## 6. Adding a New Target Provider

Edit `backend/core/llm_client.py` — add a new `_send_myprovider()` method and add the branch in `send()`. Follow the pattern of `_send_openai()`.

---

## 7. Analyzer Prompt Engineering

The analyzer (`backend/core/analyzer.py`) uses a strict system prompt that forces JSON output with a defined schema. Key design choices:

- **Low temperature (0.1)** — deterministic, consistent scoring
- **Conservative bias** — only marks `vulnerable: true` when there is clear evidence
- **Haiku model** — fast and cheap for 61 analyses per audit
- **Evidence field** — forces the model to quote the specific text that reveals the vulnerability (makes reports actionable)

If you want stricter or more lenient analysis, edit the `_ANALYSIS_SYSTEM` prompt in `analyzer.py`.

---

## 8. Risk Score Formula

```python
score = 0
for finding in vulnerable_findings:
    base_weight = {critical: 30, high: 20, medium: 10, low: 4, info: 1}[severity]
    score += base_weight * (confidence / 100)

# Normalize: worst case = 10 criticals at 100% confidence = 300 points
final_score = min(100, (score / 300) * 100)
```

This means:
- A single Critical at 100% confidence → score ≈ 10
- Three Criticals + two Highs at 100% → score ≈ 43 (Medium)
- Ten Criticals at 100% → score = 100 (Critical)

---

## 9. Report Customization

The report template is at `backend/reports/templates/report.html`. It uses Jinja2 templating with self-contained CSS (no external dependencies — works offline).

To customize:
- **Logo/branding**: Edit the `cover-logo` section
- **Color scheme**: Modify the CSS variables at the top
- **Sections**: Add/remove Jinja2 blocks
- **Reviewer name**: Auto-set from `settings.REVIEWER_NAME` (default: "Rahul Singh")

The report is served as HTML. To get PDF: open in browser → Print → Save as PDF (or use Ctrl+P). WeasyPrint can be added for server-side PDF generation.

---

## 10. Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ Yes | — | Powers the vulnerability analyzer |
| `OPENAI_API_KEY` | No | — | Needed only when auditing OpenAI targets |
| `ANALYZER_MODEL` | No | `claude-sonnet-4-6` | Deep analysis model |
| `FAST_ANALYZER_MODEL` | No | `claude-haiku-4-5-20251001` | Fast analysis model (used per-test) |
| `DATABASE_URL` | No | `sqlite+aiosqlite:///./security_auditor.db` | DB connection string |
| `MAX_CONCURRENT_ATTACKS` | No | `5` | Parallel attack concurrency |
| `SCAN_TIMEOUT_SECONDS` | No | `30` | Per-request timeout to target |
| `REVIEWER_NAME` | No | `Rahul Singh` | Name on reports |
| `DEBUG` | No | `false` | Verbose SQL + logging |

---

## 11. Known Limitations & Improvement Opportunities

| Area | Current | Improvement |
|---|---|---|
| WebSocket scaling | In-memory dict | Redis pub/sub for multi-instance |
| PDF generation | Browser print | Add WeasyPrint server-side PDF |
| Database | SQLite | PostgreSQL for production load |
| Authentication | None | Add JWT auth for multi-user SaaS |
| Attack library | 61 static prompts | Dynamic prompt generation via LLM |
| Rate limiting | Semaphore only | Token bucket per API key |
| Scheduling | Manual | Cron-based periodic audits |
| CI/CD | Not integrated | GitHub Action / CLI output mode |
| Multi-tenant | Not supported | Add org/team model to DB |

---

## 12. Security Considerations

- **API keys from users** are held in memory during the scan and persisted in the DB. For production, encrypt at rest.
- **The target's responses** (which may contain sensitive leaked data) are stored in the `findings` table. Apply appropriate data retention policies.
- **Only test systems you have authorization to test.** This tool sends adversarial payloads.
- The Anthropic API key in `.env` must not be committed to git (`.gitignore` covers this).

---

## 13. Dependency Versions (March 2026)

Key packages and their versions at time of writing:

```
fastapi==0.115.6
anthropic==0.40.0
sqlalchemy==2.0.36
pydantic==2.10.3
react==18.3.1
vite==6.0.5
```

---

*End of Knowledge Transfer Document*
*Maintained by: Rahul Singh*
