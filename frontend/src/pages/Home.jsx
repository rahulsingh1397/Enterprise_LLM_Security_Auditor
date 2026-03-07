import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../services/api'
import RiskGauge from '../components/RiskGauge'

function StatusBadge({ status }) {
  return <span className={`badge badge-${status}`}>{status}</span>
}

function RiskBadge({ level }) {
  if (!level) return null
  const map = { Critical: 'critical', High: 'high', Medium: 'medium', Low: 'low', Minimal: 'low' }
  return <span className={`badge badge-${map[level] ?? 'info'}`}>{level}</span>
}

export default function Home() {
  const [audits, setAudits]   = useState([])
  const [loading, setLoading] = useState(true)
  const [health, setHealth]   = useState(null)

  useEffect(() => {
    Promise.all([api.listAudits(0, 5), api.health()])
      .then(([a, h]) => { setAudits(a); setHealth(h) })
      .finally(() => setLoading(false))
  }, [])

  const completed = audits.filter(a => a.status === 'completed')
  const running   = audits.filter(a => a.status === 'running')
  const avgScore  = completed.length
    ? Math.round(completed.reduce((s, a) => s + (a.risk_score ?? 0), 0) / completed.length)
    : null
  const highRisk = completed.filter(a => (a.risk_score ?? 0) >= 61).length

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>🛡️ Security Dashboard</h1>
          <p>Enterprise LLM Security Auditor — automated red-team testing</p>
        </div>
        <Link to="/audit/new" className="btn btn-primary btn-lg">
          + New Audit
        </Link>
      </div>

      {/* Health banner */}
      {health && (
        <div className="alert alert-success mb-24" style={{ marginBottom: 24 }}>
          ✓ API Online — {health.app} {health.version}
        </div>
      )}

      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value text-blue">{audits.length}</div>
          <div className="stat-label">Total Audits</div>
        </div>
        <div className="stat-card">
          <div className="stat-value text-green">{completed.length}</div>
          <div className="stat-label">Completed</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: running.length > 0 ? 'var(--blue)' : 'var(--text-dim)' }}>
            {running.length}
          </div>
          <div className="stat-label">Running</div>
        </div>
        <div className="stat-card">
          <div className="stat-value text-yellow">{avgScore ?? '—'}</div>
          <div className="stat-label">Avg Risk Score</div>
          <div className="stat-sub">0-100 scale</div>
        </div>
        <div className="stat-card">
          <div className="stat-value text-red">{highRisk}</div>
          <div className="stat-label">High Risk Targets</div>
          <div className="stat-sub">score ≥ 61</div>
        </div>
      </div>

      {/* Recent audits */}
      <div className="card">
        <div className="flex-between mb-16">
          <h3>Recent Audits</h3>
          <Link to="/history" className="btn btn-ghost btn-sm">View all →</Link>
        </div>

        {loading && (
          <div className="empty-state">
            <div className="spinner spinner-lg" style={{ margin: '0 auto' }} />
          </div>
        )}

        {!loading && audits.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">🔍</div>
            <h3>No audits yet</h3>
            <p>Run your first LLM security audit to get started.</p>
            <Link to="/audit/new" className="btn btn-primary" style={{ marginTop: 16 }}>
              Start First Audit
            </Link>
          </div>
        )}

        {!loading && audits.length > 0 && (
          <table className="data-table">
            <thead>
              <tr>
                <th>Company</th>
                <th>Model</th>
                <th>Risk Score</th>
                <th>Risk Level</th>
                <th>Status</th>
                <th>Vulns</th>
                <th>Date</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {audits.map(a => (
                <tr key={a.id}>
                  <td><strong>{a.company_name}</strong></td>
                  <td className="font-mono text-sm text-muted">{a.target_model ?? '—'}</td>
                  <td>
                    {a.risk_score != null
                      ? <span style={{ fontWeight: 700 }}>{a.risk_score}</span>
                      : <span className="text-dim">—</span>
                    }
                  </td>
                  <td><RiskBadge level={a.risk_level} /></td>
                  <td><StatusBadge status={a.status} /></td>
                  <td>
                    {a.status === 'completed'
                      ? <span className="text-red font-bold">{a.vulnerabilities_found}</span>
                      : '—'
                    }
                  </td>
                  <td className="text-muted text-sm">
                    {new Date(a.created_at).toLocaleDateString()}
                  </td>
                  <td>
                    <Link to={`/audit/${a.id}`} className="btn btn-ghost btn-sm">
                      View →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* About section */}
      <div className="card" style={{ marginTop: 24 }}>
        <h3 style={{ marginBottom: 16 }}>🧪 What We Test</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 12 }}>
          {[
            { icon: '💉', title: 'Prompt Injection', desc: '12 attack variants targeting instruction override' },
            { icon: '🔓', title: 'System Prompt Leakage', desc: 'Attempts to extract confidential system context' },
            { icon: '📤', title: 'Data Leakage', desc: 'Tests for unauthorized knowledge base disclosure' },
            { icon: '🎭', title: 'Jailbreak Attacks', desc: 'DAN, developer mode, persona injection, etc.' },
            { icon: '👤', title: 'PII Exposure', desc: 'Probes for personal data in model outputs' },
            { icon: '📚', title: 'RAG Security', desc: 'Document store enumeration & injection vectors' },
          ].map(({ icon, title, desc }) => (
            <div key={title} className="card-sm">
              <div style={{ fontSize: '1.4rem', marginBottom: 8 }}>{icon}</div>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>{title}</div>
              <div className="text-sm text-muted">{desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
