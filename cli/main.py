"""
Enterprise LLM Security Auditor — CLI
Usage: python -m cli.main [COMMAND] [OPTIONS]
"""

import asyncio
import json
import sys
import time
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table
from rich import box

app = typer.Typer(
    name="llm-audit",
    help="Enterprise LLM Security Auditor CLI — automated red-team testing for LLM applications.",
    add_completion=False,
)
console = Console()

DEFAULT_API = "http://localhost:8000"


def _api(base: str, path: str) -> str:
    return f"{base.rstrip('/')}{path}"


def _severity_color(sev: str) -> str:
    return {"critical": "red", "high": "yellow", "medium": "cyan", "low": "green", "info": "blue"}.get(
        sev.lower(), "white"
    )


# ── audit command ─────────────────────────────────────────────────────────────

@app.command()
def audit(
    url: str = typer.Option(..., "--url", "-u", help="Target LLM endpoint URL"),
    company: str = typer.Option(..., "--company", "-c", help="Company name for the report"),
    provider: str = typer.Option("openai", "--provider", "-p", help="openai | anthropic | custom"),
    model: str = typer.Option("gpt-4o-mini", "--model", "-m", help="Target model name"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="Target LLM API key"),
    categories: str = typer.Option(
        "prompt_injection,jailbreak,data_leakage,pii_detection,system_prompt,rag_security",
        "--categories", help="Comma-separated scan categories"
    ),
    system_prompt: Optional[str] = typer.Option(None, "--system-prompt", "-s", help="System prompt hint"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save JSON results to file"),
    api_base: str = typer.Option(DEFAULT_API, "--api-base", hidden=True),
):
    """Run a full LLM security audit and stream live results."""

    scan_cats = [c.strip() for c in categories.split(",") if c.strip()]

    payload = {
        "company_name": company,
        "target": {
            "url": url,
            "provider": provider,
            "model": model,
            "api_key": api_key,
            "system_prompt_hint": system_prompt,
        },
        "scan_categories": scan_cats,
    }

    console.print(Panel.fit(
        f"[bold cyan]Enterprise LLM Security Auditor[/bold cyan]\n"
        f"Target: [yellow]{url}[/yellow]  Model: [yellow]{model}[/yellow]\n"
        f"Company: [green]{company}[/green]  Categories: [dim]{', '.join(scan_cats)}[/dim]",
        title="Starting Audit",
    ))

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(_api(api_base, "/api/audits/"), json=payload)
            resp.raise_for_status()
            audit_data = resp.json()
            audit_id = audit_data["id"]
    except Exception as exc:
        console.print(f"[red]Failed to create audit: {exc}[/red]")
        raise typer.Exit(1)

    console.print(f"[dim]Audit ID: {audit_id}[/dim]")

    # Poll until complete
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Running security tests...", total=100)

        while True:
            time.sleep(3)
            try:
                with httpx.Client(timeout=10) as client:
                    r = client.get(_api(api_base, f"/api/audits/{audit_id}"))
                    r.raise_for_status()
                    data = r.json()
            except Exception:
                continue

            status = data.get("status")
            total = data.get("total_tests", 1) or 1
            completed_count = data.get("vulnerabilities_found", 0) + data.get("tests_passed", 0)
            pct = min(100, round((completed_count / total) * 100))
            progress.update(task, completed=pct, description=f"[cyan]{status}[/cyan]...")

            if status in ("completed", "failed"):
                break

    _print_results(data, api_base, audit_id, output)


def _print_results(data: dict, api_base: str, audit_id: str, output: Optional[str]):
    status = data.get("status")
    risk_score = data.get("risk_score") or 0
    risk_level = data.get("risk_level") or "N/A"
    vuln = data.get("vulnerabilities_found", 0)
    total = data.get("total_tests", 0)

    if status == "failed":
        console.print(f"\n[red]Audit FAILED: {data.get('error_message')}[/red]")
        raise typer.Exit(1)

    level_color = {"Critical": "red", "High": "yellow", "Medium": "cyan", "Low": "green", "Minimal": "green"}.get(
        risk_level, "white"
    )

    console.print(f"\n[bold green]Audit Complete![/bold green]")
    console.print(Panel.fit(
        f"Risk Score: [{level_color}][bold]{risk_score:.1f} / 100[/bold][/{level_color}]\n"
        f"Risk Level: [{level_color}][bold]{risk_level}[/bold][/{level_color}]\n"
        f"Vulnerabilities: [red]{vuln}[/red] / {total} tests",
        title="Results Summary",
    ))

    # Fetch findings
    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(_api(api_base, f"/api/audits/{audit_id}/findings"))
            r.raise_for_status()
            findings = r.json()
    except Exception:
        findings = []

    vuln_findings = [f for f in findings if f.get("vulnerable")]
    if vuln_findings:
        table = Table(title="Vulnerabilities Found", box=box.ROUNDED, show_lines=True)
        table.add_column("Severity", style="bold", width=10)
        table.add_column("Attack", width=30)
        table.add_column("Scanner", width=20)
        table.add_column("Confidence", width=12)
        table.add_column("Evidence", width=40)

        for f in sorted(vuln_findings, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}.get(x.get("severity", "info"), 4)):
            sev = f.get("severity", "info")
            color = _severity_color(sev)
            table.add_row(
                f"[{color}]{sev.upper()}[/{color}]",
                f.get("attack_name", ""),
                f.get("scanner_name", ""),
                f"{f.get('confidence', 0)}%",
                (f.get("evidence") or f.get("explanation") or "")[:100],
            )
        console.print(table)
    else:
        console.print("[green]No vulnerabilities detected.[/green]")

    console.print(f"\n[dim]Report: {api_base}/api/reports/{audit_id}/html[/dim]")
    console.print(f"[dim]JSON Export: {api_base}/api/audits/{audit_id}/export/json[/dim]")

    if output:
        try:
            with httpx.Client(timeout=10) as client:
                r = client.get(_api(api_base, f"/api/audits/{audit_id}/export/json"))
                r.raise_for_status()
            with open(output, "wb") as f:
                f.write(r.content)
            console.print(f"[green]Results saved to {output}[/green]")
        except Exception as exc:
            console.print(f"[yellow]Warning: could not save output: {exc}[/yellow]")


# ── list command ──────────────────────────────────────────────────────────────

@app.command(name="list")
def list_audits(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of audits to show"),
    api_base: str = typer.Option(DEFAULT_API, "--api-base", hidden=True),
):
    """List recent audits."""
    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(_api(api_base, f"/api/audits/?limit={limit}"))
            r.raise_for_status()
            audits = r.json()
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
        raise typer.Exit(1)

    table = Table(title="Recent Audits", box=box.ROUNDED)
    table.add_column("ID", width=10)
    table.add_column("Company", width=25)
    table.add_column("Status", width=12)
    table.add_column("Risk Level", width=12)
    table.add_column("Score", width=8)
    table.add_column("Vulns", width=6)
    table.add_column("Date", width=22)

    for a in audits:
        risk = a.get("risk_level") or "—"
        color = {"Critical": "red", "High": "yellow", "Medium": "cyan", "Low": "green", "Minimal": "green"}.get(risk, "dim")
        table.add_row(
            a["id"][:8],
            a.get("company_name", ""),
            a.get("status", ""),
            f"[{color}]{risk}[/{color}]",
            f"{a['risk_score']:.1f}" if a.get("risk_score") else "—",
            str(a.get("vulnerabilities_found", 0)),
            (a.get("created_at") or "")[:19],
        )

    console.print(table)


# ── status command ────────────────────────────────────────────────────────────

@app.command()
def status(
    audit_id: str = typer.Argument(..., help="Audit ID to check"),
    api_base: str = typer.Option(DEFAULT_API, "--api-base", hidden=True),
):
    """Check the status of a specific audit."""
    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(_api(api_base, f"/api/audits/{audit_id}"))
            r.raise_for_status()
            data = r.json()
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
        raise typer.Exit(1)

    console.print_json(json.dumps(data, indent=2, default=str))


# ── report command ────────────────────────────────────────────────────────────

@app.command()
def report(
    audit_id: str = typer.Argument(..., help="Audit ID"),
    format: str = typer.Option("html", "--format", "-f", help="html | json | csv | xlsx"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    api_base: str = typer.Option(DEFAULT_API, "--api-base", hidden=True),
):
    """Download an audit report."""
    path_map = {
        "html": f"/api/reports/{audit_id}/html",
        "json": f"/api/audits/{audit_id}/export/json",
        "csv": f"/api/audits/{audit_id}/export/csv",
        "xlsx": f"/api/audits/{audit_id}/export/xlsx",
    }
    if format not in path_map:
        console.print(f"[red]Unknown format: {format}. Use html|json|csv|xlsx[/red]")
        raise typer.Exit(1)

    try:
        with httpx.Client(timeout=30) as client:
            r = client.get(_api(api_base, path_map[format]))
            r.raise_for_status()
            content = r.content
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
        raise typer.Exit(1)

    if output:
        with open(output, "wb") as f:
            f.write(content)
        console.print(f"[green]Report saved to {output}[/green]")
    else:
        if format in ("html", "json", "csv"):
            console.print(content.decode("utf-8", errors="replace"))
        else:
            console.print("[yellow]Binary format — use --output to save to file[/yellow]")


# ── delete command ────────────────────────────────────────────────────────────

@app.command()
def delete(
    audit_id: str = typer.Argument(..., help="Audit ID to delete"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    api_base: str = typer.Option(DEFAULT_API, "--api-base", hidden=True),
):
    """Delete an audit and all its findings."""
    if not yes:
        confirmed = typer.confirm(f"Delete audit {audit_id}? This cannot be undone.")
        if not confirmed:
            raise typer.Abort()

    try:
        with httpx.Client(timeout=10) as client:
            r = client.delete(_api(api_base, f"/api/audits/{audit_id}"))
            r.raise_for_status()
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Audit {audit_id} deleted.[/green]")


# ── health command ────────────────────────────────────────────────────────────

@app.command()
def health(
    api_base: str = typer.Option(DEFAULT_API, "--api-base", hidden=True),
):
    """Check API server health."""
    try:
        with httpx.Client(timeout=5) as client:
            r = client.get(_api(api_base, "/api/health"))
            r.raise_for_status()
            console.print_json(json.dumps(r.json()))
    except Exception as exc:
        console.print(f"[red]Server unreachable: {exc}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
