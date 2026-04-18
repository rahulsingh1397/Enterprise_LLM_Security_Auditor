"""
HTML Report Generator.
Renders a professional audit report using Jinja2.
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader

from utils.config import settings

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=True)


def _severity_color(severity: str) -> str:
    return {
        "critical": "#f85149",
        "high": "#d29922",
        "medium": "#388bfd",
        "low": "#3fb950",
        "info": "#8b949e",
    }.get(severity.lower(), "#8b949e")


def _risk_color(level: str) -> str:
    return {
        "Critical": "#f85149",
        "High": "#d29922",
        "Medium": "#388bfd",
        "Low": "#3fb950",
        "Minimal": "#3fb950",
    }.get(level, "#8b949e")


def generate_html_report(audit, findings: List) -> str:
    """Render the HTML report for the given audit and findings."""
    template = _env.get_template("report.html")

    vuln_findings = [f for f in findings if f.vulnerable]
    safe_findings = [f for f in findings if not f.vulnerable]

    # Group by category
    categories: dict = {}
    for f in findings:
        categories.setdefault(f.category, []).append(f)

    # Severity breakdown
    severity_counts = {
        "critical": sum(1 for f in vuln_findings if f.severity == "critical"),
        "high": sum(1 for f in vuln_findings if f.severity == "high"),
        "medium": sum(1 for f in vuln_findings if f.severity == "medium"),
        "low": sum(1 for f in vuln_findings if f.severity == "low"),
        "info": sum(1 for f in vuln_findings if f.severity == "info"),
    }

    report_date = datetime.now(timezone.utc).strftime("%B %d, %Y")
    if audit.completed_at:
        report_date = audit.completed_at.strftime("%B %d, %Y")

    ctx = {
        "company_name": audit.company_name,
        "report_date": report_date,
        "reviewer_name": audit.reviewer_name or settings.REVIEWER_NAME,
        "audit_id": audit.id,
        "target_url": audit.target_url,
        "target_provider": audit.target_provider,
        "target_model": audit.target_model,
        "status": audit.status,
        "risk_score": audit.risk_score or 0,
        "risk_level": audit.risk_level or "Unknown",
        "risk_color": _risk_color(audit.risk_level or ""),
        "total_tests": audit.total_tests,
        "vulnerabilities_found": audit.vulnerabilities_found,
        "tests_passed": audit.tests_passed,
        "summary": audit.summary or "",
        "vuln_findings": vuln_findings,
        "safe_findings": safe_findings,
        "categories": categories,
        "severity_counts": severity_counts,
        "severity_color": _severity_color,
        "created_at": audit.created_at.strftime("%Y-%m-%d %H:%M UTC") if audit.created_at else "",
    }

    return template.render(**ctx)
