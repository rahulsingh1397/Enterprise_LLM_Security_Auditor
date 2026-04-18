"""
Main audit orchestrator.
Runs all enabled scanners against the target LLM and persists results.
"""

import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator, Callable, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.analyzer import analyze_response
from core.dynamic_attacks import generate_dynamic_attacks
from core.llm_client import TargetLLMClient
from core.risk_scorer import (
    calculate_risk_score,
    generate_executive_summary,
    get_risk_level,
)
from db import models as db_models
from models.audit import AuditCreateRequest, ProgressEvent
from models.vulnerability import FindingCreate
from scanners.data_leakage import DataLeakageScanner
from scanners.jailbreak import JailbreakScanner
from scanners.pii_detection import PIIDetectionScanner
from scanners.prompt_injection import PromptInjectionScanner
from scanners.rag_security import RAGSecurityScanner
from scanners.system_prompt import SystemPromptScanner
from scanners.encoding_obfuscation import EncodingObfuscationScanner
from utils.config import settings
from utils.email import send_audit_complete_alert, send_critical_finding_alert
from utils.logger import get_logger

logger = get_logger(__name__)

_SCANNER_REGISTRY = {
    "prompt_injection": PromptInjectionScanner,
    "system_prompt_leakage": SystemPromptScanner,
    "data_leakage": DataLeakageScanner,
    "jailbreak": JailbreakScanner,
    "pii_exposure": PIIDetectionScanner,
    "rag_security": RAGSecurityScanner,
    "encoding_obfuscation": EncodingObfuscationScanner,
}


class AuditOrchestrator:
    def __init__(self, db: AsyncSession, notify_email: Optional[str] = None):
        self.db = db
        self.notify_email = notify_email

    async def run(
        self,
        audit_id: str,
        request: AuditCreateRequest,
        progress_callback: Optional[Callable[[ProgressEvent], None]] = None,
    ) -> db_models.AuditRecord:
        logger.info("Starting audit %s for %s", audit_id, request.company_name)

        # Mark as running
        record = await self.db.get(db_models.AuditRecord, audit_id)
        record.status = "running"
        await self.db.commit()

        target_client = TargetLLMClient(request.target)
        scanners = [
            _SCANNER_REGISTRY[cat]()
            for cat in request.scan_categories
            if cat in _SCANNER_REGISTRY
        ]

        all_attack_prompts = [
            (scanner, attack)
            for scanner in scanners
            for attack in scanner.attacks
        ]

        # Inject dynamic Claude-generated attacks if enabled
        if settings.DYNAMIC_ATTACKS_ENABLED:
            dynamic = await generate_dynamic_attacks(
                system_prompt_hint=request.target.system_prompt_hint,
                company_name=request.company_name,
                scan_categories=request.scan_categories,
                count=settings.DYNAMIC_ATTACKS_PER_SCAN,
            )
            if dynamic:
                # Use first matching scanner for dynamic attacks; fallback to prompt injection
                default_scanner = scanners[0] if scanners else PromptInjectionScanner()
                for d_attack in dynamic:
                    all_attack_prompts.append((default_scanner, d_attack))
                logger.info("Added %d dynamic attacks", len(dynamic))

        total = len(all_attack_prompts)
        record.total_tests = total
        await self.db.commit()

        completed = 0
        all_findings: List[FindingCreate] = []

        try:
            semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_ATTACKS)

            async def _run_single(scanner, attack):
                nonlocal completed
                async with semaphore:
                    try:
                        response = await target_client.send(attack["prompt"])
                        analysis = await analyze_response(
                            attack_type=scanner.category,
                            attack_name=attack["name"],
                            attack_prompt=attack["prompt"],
                            target_response=response,
                        )
                    except Exception as exc:
                        logger.error("Attack %s failed: %s", attack["name"], exc)
                        response = f"[ERROR] {exc}"
                        from backend.models.vulnerability import AnalysisResult
                        analysis = AnalysisResult(
                            vulnerable=False,
                            confidence=0,
                            severity="info",
                            explanation="Test failed to execute.",
                            recommendation="Check target connectivity.",
                        )

                    finding = FindingCreate(
                        audit_id=audit_id,
                        scanner_name=scanner.name,
                        attack_name=attack["name"],
                        attack_prompt=attack["prompt"],
                        target_response=response,
                        vulnerable=analysis.vulnerable,
                        severity=analysis.severity,
                        confidence=analysis.confidence,
                        evidence=analysis.evidence,
                        explanation=analysis.explanation,
                        recommendation=analysis.recommendation,
                        category=scanner.category,
                    )
                    all_findings.append(finding)

                    # Persist finding
                    db_finding = db_models.FindingRecord(**finding.model_dump())
                    self.db.add(db_finding)
                    await self.db.commit()

                    # Email alert for critical/high findings
                    if analysis.vulnerable and analysis.severity in ("critical", "high") and self.notify_email:
                        asyncio.create_task(send_critical_finding_alert(
                            to=self.notify_email,
                            company_name=request.company_name,
                            audit_id=audit_id,
                            attack_name=attack["name"],
                            severity=analysis.severity,
                            explanation=analysis.explanation,
                        ))

                    completed += 1
                    if progress_callback:
                        event = ProgressEvent(
                            audit_id=audit_id,
                            event="progress",
                            completed=completed,
                            total=total,
                            percent=round((completed / total) * 100, 1),
                            scanner=scanner.name,
                            message=f"Tested: {attack['name']}",
                            latest_finding={
                                "attack_name": attack["name"],
                                "vulnerable": analysis.vulnerable,
                                "severity": analysis.severity,
                            } if analysis.vulnerable else None,
                        )
                        await progress_callback(event)

            # Run all attacks concurrently (bounded by semaphore)
            tasks = [_run_single(s, a) for s, a in all_attack_prompts]
            await asyncio.gather(*tasks)

            # Score
            risk_score = calculate_risk_score(all_findings)
            risk_level = get_risk_level(risk_score)
            vuln_count = sum(1 for f in all_findings if f.vulnerable)

            summary = generate_executive_summary(
                all_findings, request.company_name, risk_score, risk_level
            )

            record.status = "completed"
            record.risk_score = risk_score
            record.risk_level = risk_level
            record.vulnerabilities_found = vuln_count
            record.tests_passed = total - vuln_count
            record.summary = summary
            record.completed_at = datetime.now(timezone.utc)
            await self.db.commit()

            logger.info(
                "Audit %s complete — score=%.1f level=%s vuln=%d/%d",
                audit_id, risk_score, risk_level, vuln_count, total,
            )

            if progress_callback:
                await progress_callback(ProgressEvent(
                    audit_id=audit_id,
                    event="completed",
                    completed=total,
                    total=total,
                    percent=100.0,
                    scanner="complete",
                    message=f"Audit complete. Risk score: {risk_score}/100 ({risk_level})",
                ))

            # Send audit complete email notification
            if self.notify_email:
                asyncio.create_task(send_audit_complete_alert(
                    to=self.notify_email,
                    company_name=request.company_name,
                    audit_id=audit_id,
                    risk_score=risk_score,
                    risk_level=risk_level,
                    total_tests=total,
                    vulnerabilities_found=vuln_count,
                ))

        except Exception as exc:
            logger.exception("Audit %s failed: %s", audit_id, exc)
            record.status = "failed"
            record.error_message = str(exc)
            await self.db.commit()

            if progress_callback:
                await progress_callback(ProgressEvent(
                    audit_id=audit_id,
                    event="error",
                    completed=completed,
                    total=total,
                    percent=0,
                    scanner="error",
                    message=f"Audit failed: {exc}",
                ))

        await self.db.refresh(record)
        return record
