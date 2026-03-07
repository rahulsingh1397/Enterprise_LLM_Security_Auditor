import { useEffect, useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../services/api'
import RiskGauge from '../components/RiskGauge'
import ScanProgress from '../components/ScanProgress'
import VulnerabilityCard from '../components/VulnerabilityCard'

const SEV_ORDER = { critical: 0, high: 1, medium: 2, low: 3, info: 4 }
const CATEGORY_ICONS = {
  prompt_injection: '💉',
  system_prompt_leakage: '🔓',
  data_leakage: '📤',
  jailbreak: '🎭',
  pii_exposure: '👤',
  rag_security: '📚',
}

export default function AuditResults() {
  const { id } = useParams()
  const [audit, setAudit]       = useState(null)
  const [findings, setFindings] = useState([])
  const [loading, setLoading]   = useState(true)
  const [tab, setTab]           = useState('overview')
  const [filter, setFilter]     = useState('all')

  const load = useCallback(async () => {
    const [a, f] = await Promise.all([api.getAudit(id), api.getFindings(id)])
    setAudit(a)
    setFindings(f.sort((a, b) => (SEV_ORDER[a.severity] ?? 9) - (SEV_ORDER[b.severity] ?? 9)))
  }, [id])

  useEffect(() => {
    load().finally(() => setLoading(false))
  }, [load])

  const onScanComplete = () => {
    setTimeout(() => load(), 1500)
  }

  if (loading) return (
    <div className="empty-state">
      <div className="spinner spinner-lg" style={{ margin: '0 auto 16px' }} />
      <p>Loading audit…</p>
    </div>
  )

  if (!audit) return (
    <div className="alert alert-error">Audit not found.</div>
  )

  const vulnFindings = findings.filter(f => f.vulnerable)
  const safeFindings = findings.filter(f => !f.vulnerable)

  const sevCounts = { critical: 0, high: 0, medium: 0, low: 0, info: 0 }
  vulnFindings.forEach(f => sevCounts[f.severity] = (sevCounts[f.severity] || 0) + 1)

  const categories = [...new Set(findings.map(f => f.category))]
  const catVuln = Object.fromEntries(
    categories.map(c => [c, findings.filter(f => f.category === c && f.vulnerable).length])
  )

  const filteredVulns = filter === 'all'
    ? vulnFindings
    : vulnFindings.filter(f => f.severity === filter)

  const isRunning = audit.status === 'running' || audit.status === 'pending'

  return (
    <div>
      {/* Page header */}
      <div className="page-header">
        <div>
          <div className="flex-center gap-12 mb-8">
            <Link to="/" className="text-muted text-sm">← Dashboard</Link>
            <span className="text-dim">/</span>
            <span className="text-sm">{audit.company_name}</span>
          </div>
          <h1>{audit.company_name}</h1>
          <p className="text-muted" style={{ fontSize: '0.85rem', marginTop: 4 }}>
            {audit.target_provider?.toUpperCase()} · {audit.target_model} ·
            Reviewed by Rahul Singh · {new Date(audit.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}
          </p>
        </div>
        <div className="flex gap-12">
          {audit.status === 'completed' && (
            <a
              href={api.getReportUrl(id)}
              target="_blank"
              rel="noreferrer"
              className="btn btn-ghost"
            >
              📄 View Report
            </a>
          )}
        </div>
      </div>

      {/* Live progress (only when running) */}
      {isRunning && (
        <div style={{ marginBottom: 24 }}>
          <ScanProgress auditId={id} onComplete={onScanComplete} />
        </div>
      )}

      {/* Error state */}
      {audit.status === 'failed' && (
        <div className="alert alert-error mb-24">
          ❌ Audit failed: {audit.error_message}
        </div>
      )}

      {/* Results — only when completed */}
      {audit.status === 'completed' && (
        <>
          {/* Risk overview */}
          <div className="card mb-24" style={{
            display: 'grid',
            gridTemplateColumns: 'auto 1fr',
            gap: 40,
            alignItems: 'center',
          }}>
            <RiskGauge
              score={Math.round(audit.risk_score ?? 0)}
              level={audit.risk_level ?? 'Minimal'}
              size={200}
            />
            <div>
              <div className="stats-grid" style={{ marginBottom: 0 }}>
                {[
                  { label: 'Tests Run', val: audit.total_tests, color: 'var(--blue)' },
                  { label: 'Vulnerabilities', val: audit.vulnerabilities_found, color: 'var(--red)' },
                  { label: 'Tests Passed', val: audit.tests_passed, color: 'var(--green)' },
                ].map(({ label, val, color }) => (
                  <div key={label} className="stat-card">
                    <div className="stat-value" style={{ color }}>{val}</div>
                    <div className="stat-label">{label}</div>
                  </div>
                ))}
              </div>

              {/* Severity breakdown */}
              <div style={{ marginTop: 16 }}>
                {Object.entries(sevCounts).map(([sev, count]) => (
                  count > 0 && (
                    <span key={sev} style={{ marginRight: 8 }}>
                      <span className={`badge badge-${sev}`}>{count} {sev}</span>
                    </span>
                  )
                ))}
              </div>
            </div>
          </div>

          {/* Summary */}
          {audit.summary && (
            <div className="card mb-24" style={{ borderLeft: '4px solid var(--blue)' }}>
              <h3 style={{ marginBottom: 12 }}>Executive Summary</h3>
              <p className="text-sm" style={{ lineHeight: 1.8, color: 'var(--text-muted)' }}>
                {audit.summary}
              </p>
            </div>
          )}

          {/* Tabs */}
          <div className="flex gap-8 mb-24" style={{ borderBottom: '1px solid var(--border)', paddingBottom: 0 }}>
            {[
              { key: 'overview',  label: '📊 Overview' },
              { key: 'vulns',    label: `⚠ Vulnerabilities (${vulnFindings.length})` },
              { key: 'all',      label: `📋 All Tests (${findings.length})` },
            ].map(t => (
              <button key={t.key} onClick={() => setTab(t.key)}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  padding: '10px 16px',
                  fontSize: '0.875rem',
                  fontWeight: tab === t.key ? 700 : 500,
                  color: tab === t.key ? 'var(--blue)' : 'var(--text-muted)',
                  borderBottom: tab === t.key ? '2px solid var(--blue)' : '2px solid transparent',
                  marginBottom: -1,
                  transition: 'all 0.15s',
                }}>
                {t.label}
              </button>
            ))}
          </div>

          {/* ── Overview Tab ─────────────────────────────────────── */}
          {tab === 'overview' && (
            <div>
              <h3 style={{ marginBottom: 16 }}>Results by Category</h3>
              <div style={{ display: 'grid', gap: 12 }}>
                {categories.map(cat => {
                  const catFindings = findings.filter(f => f.category === cat)
                  const catVulnCount = catVuln[cat]
                  const pct = Math.round((catVulnCount / catFindings.length) * 100)
                  return (
                    <div key={cat} className="card-sm">
                      <div className="flex-between mb-8">
                        <div className="flex-center gap-12">
                          <span style={{ fontSize: '1.2rem' }}>{CATEGORY_ICONS[cat] ?? '🔍'}</span>
                          <div>
                            <div style={{ fontWeight: 600 }}>
                              {cat.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                            </div>
                            <div className="text-xs text-muted">{catFindings.length} tests</div>
                          </div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ fontWeight: 700, color: catVulnCount > 0 ? 'var(--red)' : 'var(--green)' }}>
                            {catVulnCount} / {catFindings.length}
                          </div>
                          <div className="text-xs text-muted">vulnerable</div>
                        </div>
                      </div>
                      <div className="progress-bar-bg">
                        <div className="progress-bar-fill" style={{
                          width: `${pct}%`,
                          background: pct > 60 ? 'var(--red)' : pct > 30 ? 'var(--yellow)' : 'var(--green)',
                        }} />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* ── Vulnerabilities Tab ──────────────────────────────── */}
          {tab === 'vulns' && (
            <div>
              {vulnFindings.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">✅</div>
                  <h3>No vulnerabilities detected</h3>
                  <p>The target LLM passed all security tests.</p>
                </div>
              ) : (
                <>
                  <div className="flex-between mb-16">
                    <h3>{vulnFindings.length} Confirmed Vulnerabilities</h3>
                    <select className="form-select" style={{ width: 160 }} value={filter}
                      onChange={e => setFilter(e.target.value)}>
                      <option value="all">All Severities</option>
                      <option value="critical">Critical</option>
                      <option value="high">High</option>
                      <option value="medium">Medium</option>
                      <option value="low">Low</option>
                    </select>
                  </div>
                  {filteredVulns.map((f, i) => (
                    <VulnerabilityCard key={f.id} finding={f} index={i + 1} />
                  ))}
                </>
              )}
            </div>
          )}

          {/* ── All Tests Tab ─────────────────────────────────────── */}
          {tab === 'all' && (
            <div className="card" style={{ padding: 0 }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Test</th>
                    <th>Scanner</th>
                    <th>Result</th>
                    <th>Severity</th>
                    <th>Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {findings.map((f, i) => (
                    <tr key={f.id}>
                      <td className="text-dim font-mono text-xs">{String(i + 1).padStart(2, '0')}</td>
                      <td><strong style={{ fontSize: '0.875rem' }}>{f.attack_name}</strong></td>
                      <td className="text-muted text-sm">{f.scanner_name}</td>
                      <td>
                        {f.vulnerable
                          ? <span style={{ color: 'var(--red)', fontWeight: 700 }}>⚠ VULNERABLE</span>
                          : <span style={{ color: 'var(--green)', fontWeight: 700 }}>✓ SAFE</span>
                        }
                      </td>
                      <td>
                        {f.vulnerable
                          ? <span className={`badge badge-${f.severity}`}>{f.severity}</span>
                          : <span className="text-dim">—</span>
                        }
                      </td>
                      <td className="text-muted text-sm">{f.vulnerable ? `${f.confidence}%` : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  )
}
