import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../services/api'

function RiskBar({ score, level }) {
  const COLORS = {
    Critical: '#f85149', High: '#d29922', Medium: '#388bfd', Low: '#3fb950', Minimal: '#3fb950',
  }
  const color = COLORS[level] ?? '#8b949e'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <div style={{ width: 80, height: 6, background: 'var(--bg-overlay)', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{ width: `${score ?? 0}%`, height: '100%', background: color, borderRadius: 3 }} />
      </div>
      <span style={{ fontSize: '0.8rem', fontWeight: 700, color }}>{score ?? '—'}</span>
    </div>
  )
}

export default function History() {
  const [audits, setAudits]     = useState([])
  const [loading, setLoading]   = useState(true)
  const [deleting, setDeleting] = useState(null)
  const [page, setPage]         = useState(0)
  const PAGE = 20

  const load = () => {
    setLoading(true)
    api.listAudits(page * PAGE, PAGE)
      .then(setAudits)
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [page])

  async function handleDelete(id) {
    if (!confirm('Delete this audit and all its findings?')) return
    setDeleting(id)
    try {
      await api.deleteAudit(id)
      setAudits(a => a.filter(x => x.id !== id))
    } catch (e) {
      alert(e.message)
    } finally {
      setDeleting(null)
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>📋 Audit History</h1>
          <p>All past and ongoing LLM security audits</p>
        </div>
        <Link to="/audit/new" className="btn btn-primary">+ New Audit</Link>
      </div>

      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <div className="empty-state"><div className="spinner spinner-lg" style={{ margin: '0 auto' }} /></div>
        ) : audits.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📋</div>
            <h3>No audits found</h3>
            <p>Run your first security audit to see results here.</p>
            <Link to="/audit/new" className="btn btn-primary" style={{ marginTop: 16 }}>Start Audit</Link>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Company</th>
                <th>Provider / Model</th>
                <th>Status</th>
                <th>Risk Score</th>
                <th>Vulns</th>
                <th>Tests</th>
                <th>Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {audits.map(a => (
                <tr key={a.id}>
                  <td>
                    <Link to={`/audit/${a.id}`} style={{ fontWeight: 600 }}>
                      {a.company_name}
                    </Link>
                    <div className="text-xs text-dim font-mono" style={{ marginTop: 2 }}>
                      {a.id.slice(0, 8)}…
                    </div>
                  </td>
                  <td className="text-sm text-muted">
                    <div>{a.target_provider?.toUpperCase()}</div>
                    <div className="font-mono text-xs">{a.target_model}</div>
                  </td>
                  <td>
                    <span className={`badge badge-${a.status}`}>{a.status}</span>
                  </td>
                  <td>
                    {a.status === 'completed'
                      ? <RiskBar score={a.risk_score} level={a.risk_level} />
                      : <span className="text-dim">—</span>
                    }
                  </td>
                  <td>
                    {a.status === 'completed'
                      ? <span style={{ fontWeight: 700, color: a.vulnerabilities_found > 0 ? 'var(--red)' : 'var(--green)' }}>
                          {a.vulnerabilities_found}
                        </span>
                      : '—'
                    }
                  </td>
                  <td className="text-muted text-sm">{a.total_tests || '—'}</td>
                  <td className="text-muted text-sm">
                    {new Date(a.created_at).toLocaleDateString('en-GB', {
                      day: '2-digit', month: 'short', year: 'numeric'
                    })}
                  </td>
                  <td>
                    <div className="flex gap-8">
                      <Link to={`/audit/${a.id}`} className="btn btn-ghost btn-sm">View</Link>
                      {a.status === 'completed' && (
                        <a href={api.getReportUrl(a.id)} target="_blank" rel="noreferrer"
                          className="btn btn-ghost btn-sm">
                          Report
                        </a>
                      )}
                      <button className="btn btn-danger btn-sm"
                        disabled={deleting === a.id}
                        onClick={() => handleDelete(a.id)}>
                        {deleting === a.id ? '…' : 'Delete'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {audits.length === PAGE && (
        <div className="flex gap-12 mt-16" style={{ justifyContent: 'center' }}>
          <button className="btn btn-ghost btn-sm" disabled={page === 0} onClick={() => setPage(p => p - 1)}>
            ← Previous
          </button>
          <span className="text-muted text-sm" style={{ alignSelf: 'center' }}>Page {page + 1}</span>
          <button className="btn btn-ghost btn-sm" onClick={() => setPage(p => p + 1)}>
            Next →
          </button>
        </div>
      )}
    </div>
  )
}
