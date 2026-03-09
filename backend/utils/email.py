"""
Email notification utilities (aiosmtplib).
Sends alerts when critical vulnerabilities are found.
"""

import logging
from typing import Optional

from backend.utils.config import settings

logger = logging.getLogger(__name__)


async def _send(to: str, subject: str, html_body: str) -> None:
    """Low-level async SMTP sender."""
    if not settings.SMTP_HOST or not settings.SMTP_USERNAME:
        logger.debug("SMTP not configured — skipping email to %s", to)
        return

    try:
        import aiosmtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to
        msg.attach(MIMEText(html_body, "html"))

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        logger.info("Email sent: %s → %s", subject, to)
    except Exception as exc:
        logger.warning("Failed to send email to %s: %s", to, exc)


async def send_critical_finding_alert(
    to: str,
    company_name: str,
    audit_id: str,
    attack_name: str,
    severity: str,
    explanation: str,
) -> None:
    """Alert stakeholders when a critical/high vulnerability is detected."""
    if not settings.NOTIFY_ON_CRITICAL:
        return

    subject = f"[LLM Security Alert] {severity.upper()} vulnerability found — {company_name}"
    html = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333">
    <div style="max-width:600px;margin:0 auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
      <div style="background:#c0392b;color:white;padding:20px">
        <h2 style="margin:0">&#x26A0; Security Alert: {severity.upper()} Vulnerability</h2>
      </div>
      <div style="padding:24px">
        <p><strong>Company:</strong> {company_name}</p>
        <p><strong>Audit ID:</strong> {audit_id}</p>
        <p><strong>Attack:</strong> {attack_name}</p>
        <p><strong>Severity:</strong> <span style="color:#c0392b;font-weight:bold">{severity.upper()}</span></p>
        <hr style="border:none;border-top:1px solid #eee">
        <p><strong>Explanation:</strong><br>{explanation}</p>
        <p style="margin-top:24px">
          <a href="http://localhost:5173/audits/{audit_id}"
             style="background:#2563eb;color:white;padding:10px 20px;border-radius:6px;text-decoration:none">
            View Full Report
          </a>
        </p>
      </div>
      <div style="background:#f9f9f9;padding:12px;font-size:12px;color:#777;text-align:center">
        Enterprise LLM Security Auditor — Automated Security Testing Platform
      </div>
    </div>
    </body></html>
    """
    await _send(to, subject, html)


async def send_audit_complete_alert(
    to: str,
    company_name: str,
    audit_id: str,
    risk_score: float,
    risk_level: str,
    total_tests: int,
    vulnerabilities_found: int,
) -> None:
    """Notify when an audit finishes."""
    color = {
        "Critical": "#c0392b", "High": "#e67e22",
        "Medium": "#f1c40f", "Low": "#27ae60", "Minimal": "#2ecc71"
    }.get(risk_level, "#666")

    subject = f"[LLM Audit Complete] {company_name} — Risk: {risk_level} ({risk_score:.1f}/100)"
    html = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333">
    <div style="max-width:600px;margin:0 auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
      <div style="background:#1e293b;color:white;padding:20px">
        <h2 style="margin:0">LLM Security Audit Complete</h2>
      </div>
      <div style="padding:24px">
        <p><strong>Company:</strong> {company_name}</p>
        <table style="width:100%;border-collapse:collapse;margin:16px 0">
          <tr>
            <td style="padding:8px;background:#f8f9fa;border:1px solid #e0e0e0"><strong>Risk Score</strong></td>
            <td style="padding:8px;border:1px solid #e0e0e0;color:{color};font-weight:bold">{risk_score:.1f} / 100</td>
          </tr>
          <tr>
            <td style="padding:8px;background:#f8f9fa;border:1px solid #e0e0e0"><strong>Risk Level</strong></td>
            <td style="padding:8px;border:1px solid #e0e0e0;color:{color};font-weight:bold">{risk_level}</td>
          </tr>
          <tr>
            <td style="padding:8px;background:#f8f9fa;border:1px solid #e0e0e0"><strong>Total Tests</strong></td>
            <td style="padding:8px;border:1px solid #e0e0e0">{total_tests}</td>
          </tr>
          <tr>
            <td style="padding:8px;background:#f8f9fa;border:1px solid #e0e0e0"><strong>Vulnerabilities Found</strong></td>
            <td style="padding:8px;border:1px solid #e0e0e0;color:#c0392b;font-weight:bold">{vulnerabilities_found}</td>
          </tr>
        </table>
        <p style="margin-top:24px">
          <a href="http://localhost:5173/audits/{audit_id}"
             style="background:#2563eb;color:white;padding:10px 20px;border-radius:6px;text-decoration:none">
            View Full Report
          </a>
        </p>
      </div>
      <div style="background:#f9f9f9;padding:12px;font-size:12px;color:#777;text-align:center">
        Enterprise LLM Security Auditor — Automated Security Testing Platform
      </div>
    </div>
    </body></html>
    """
    await _send(to, subject, html)
