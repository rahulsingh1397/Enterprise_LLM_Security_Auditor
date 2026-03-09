import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api'

export default function Templates() {
  const [templates, setTemplates] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    api.listTemplates()
      .then(setTemplates)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const handleUse = (template) => {
    // Store the selected template and navigate to new audit wizard
    sessionStorage.setItem('audit_template', JSON.stringify(template))
    navigate('/audit/new')
  }

  const categoryLabels = {
    prompt_injection: 'Prompt Injection',
    system_prompt: 'System Prompt Leak',
    data_leakage: 'Data Leakage',
    jailbreak: 'Jailbreak',
    pii_detection: 'PII Exposure',
    rag_security: 'RAG Security',
  }

  const severityColor = (cat) => {
    const colors = {
      prompt_injection: '#ef4444',
      jailbreak: '#f97316',
      data_leakage: '#eab308',
      pii_detection: '#a855f7',
      system_prompt: '#3b82f6',
      rag_security: '#06b6d4',
    }
    return colors[cat] || '#6b7280'
  }

  if (loading) return <div style={{ padding: 40, color: 'var(--text-dim)' }}>Loading templates...</div>

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto' }}>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ margin: 0, fontSize: '1.6rem', color: 'var(--text-primary)' }}>Audit Templates</h1>
        <p style={{ color: 'var(--text-dim)', marginTop: 8 }}>
          Pre-configured security tests for common LLM deployment patterns. Click <strong>Use Template</strong> to pre-fill the audit wizard.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 20 }}>
        {templates.map((t) => (
          <div key={t.id} className="card" style={{ display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
              <span style={{ fontSize: 32 }}>{t.icon}</span>
              <div>
                <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{t.name}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                  {t.target.provider} · {t.target.model}
                </div>
              </div>
            </div>

            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: '0 0 16px', lineHeight: 1.5, flexGrow: 1 }}>
              {t.description}
            </p>

            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Scan Categories ({t.scan_categories.length})
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {t.scan_categories.map((cat) => (
                  <span
                    key={cat}
                    style={{
                      padding: '3px 8px', borderRadius: 4, fontSize: '0.72rem', fontWeight: 600,
                      background: `${severityColor(cat)}20`,
                      color: severityColor(cat),
                      border: `1px solid ${severityColor(cat)}40`,
                    }}
                  >
                    {categoryLabels[cat] || cat}
                  </span>
                ))}
              </div>
            </div>

            {t.target.system_prompt_hint && (
              <div style={{ marginBottom: 16, padding: '8px 12px', background: 'var(--bg-secondary)', borderRadius: 6, fontSize: '0.78rem', color: 'var(--text-muted)', fontStyle: 'italic', borderLeft: '3px solid var(--accent)' }}>
                "{t.target.system_prompt_hint.substring(0, 100)}..."
              </div>
            )}

            <button
              onClick={() => handleUse(t)}
              style={{ padding: '10px', background: 'var(--accent)', border: 'none', borderRadius: 8, color: 'white', fontWeight: 700, cursor: 'pointer', fontSize: '0.85rem' }}
            >
              Use Template →
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
