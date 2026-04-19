import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api'

const SCAN_CATEGORIES = [
  { id: 'prompt_injection',    icon: '', label: 'Prompt Injection',     desc: '12 instruction-override attacks' },
  { id: 'system_prompt_leakage', icon: '', label: 'System Prompt Leakage', desc: '10 context-extraction probes' },
  { id: 'data_leakage',        icon: '', label: 'Data Leakage',         desc: '10 knowledge-base extraction tests' },
  { id: 'jailbreak',           icon: '', label: 'Jailbreak Attacks',    desc: '10 persona/mode bypass attacks' },
  { id: 'pii_exposure',        icon: '', label: 'PII Exposure',         desc: '9 personal data extraction probes' },
  { id: 'rag_security',        icon: '', label: 'RAG Security',         desc: '10 retrieval-store vulnerability tests' },
  { id: 'encoding_obfuscation', icon: '', label: 'Encoding & Obfuscation', desc: '6 cipher/encoding bypass attacks' },
]

const PROVIDERS = [
  { value: 'openai',    label: 'OpenAI (GPT-4, GPT-3.5, etc.)' },
  { value: 'anthropic', label: 'Anthropic (Claude)' },
  { value: 'custom',   label: 'Custom HTTP Endpoint' },
]

const PROVIDER_MODELS = {
  openai:    ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
  anthropic: ['claude-sonnet-4-6', 'claude-haiku-4-5-20251001', 'claude-opus-4-6'],
  custom:    ['custom-model'],
}

export default function NewAudit() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const [form, setForm] = useState({
    company_name: '',
    provider: 'openai',
    url: '',
    api_key: '',
    model: 'gpt-4o',
    system_prompt_hint: '',
    scan_categories: SCAN_CATEGORIES.map(c => c.id),
  })

  const set = (key) => (e) => setForm(f => ({ ...f, [key]: e.target.value }))

  const toggleCategory = (id) => {
    setForm(f => ({
      ...f,
      scan_categories: f.scan_categories.includes(id)
        ? f.scan_categories.filter(c => c !== id)
        : [...f.scan_categories, id],
    }))
  }

  const totalTests = SCAN_CATEGORIES
    .filter(c => form.scan_categories.includes(c.id))
    .reduce((s, c) => {
      const counts = { prompt_injection: 12, system_prompt_leakage: 10, data_leakage: 10, jailbreak: 10, pii_exposure: 9, rag_security: 10, encoding_obfuscation: 6 }
      return s + (counts[c.id] ?? 0)
    }, 0)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.company_name.trim()) { setError('Company name is required'); return }
    if (!form.api_key.trim()) { setError('API key is required'); return }
    if (form.scan_categories.length === 0) { setError('Select at least one scan category'); return }

    setLoading(true)
    setError(null)
    try {
      const payload = {
        company_name: form.company_name.trim(),
        target: {
          provider: form.provider,
          url: form.url.trim() || null,
          api_key: form.api_key.trim(),
          model: form.model.trim(),
          system_prompt_hint: form.system_prompt_hint.trim() || null,
        },
        scan_categories: form.scan_categories,
      }
      const audit = await api.createAudit(payload)
      navigate(`/audit/${audit.id}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>🚀 New Security Audit</h1>
          <p>Configure and launch an automated red-team assessment</p>
        </div>
      </div>

      {/* Steps indicator */}
      <div className="flex gap-8 mb-24">
        {['Target Config', 'Scan Options', 'Launch'].map((s, i) => (
          <div key={s} className="flex-center gap-8">
            <div style={{
              width: 28, height: 28, borderRadius: '50%',
              background: step > i + 1 ? 'var(--green)' : step === i + 1 ? 'var(--blue)' : 'var(--bg-overlay)',
              border: `2px solid ${step >= i + 1 ? 'transparent' : 'var(--border)'}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '0.75rem', fontWeight: 700,
              color: step >= i + 1 ? '#fff' : 'var(--text-dim)',
            }}>
              {step > i + 1 ? '✓' : i + 1}
            </div>
            <span style={{ fontSize: '0.85rem', color: step === i + 1 ? 'var(--text)' : 'var(--text-muted)', fontWeight: step === i + 1 ? 600 : 400 }}>
              {s}
            </span>
            {i < 2 && <span style={{ color: 'var(--border)', margin: '0 4px' }}>›</span>}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit}>
        {error && <div className="alert alert-error">{error}</div>}

        {/* ── Step 1: Target Config ────────────────────────────────── */}
        {step === 1 && (
          <div className="card">
            <h3 style={{ marginBottom: 24 }}>Step 1: Target LLM Configuration</h3>

            <div className="form-group">
              <label className="form-label">Company / Client Name *</label>
              <input className="form-input" value={form.company_name} onChange={set('company_name')}
                placeholder="e.g. Acme Corp" required />
              <div className="form-hint">This name will appear on the audit report.</div>
            </div>

            <div className="form-group">
              <label className="form-label">LLM Provider *</label>
              <select className="form-select" value={form.provider}
                onChange={e => {
                  const p = e.target.value
                  setForm(f => ({ ...f, provider: p, model: PROVIDER_MODELS[p][0] }))
                }}>
                {PROVIDERS.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
              </select>
            </div>

            {form.provider === 'custom' && (
              <div className="form-group">
                <label className="form-label">Endpoint URL *</label>
                <input className="form-input" value={form.url} onChange={set('url')}
                  placeholder="https://your-llm-api.com/v1/chat" />
                <div className="form-hint">Must accept POST with {'{message, system, model}'} → {'{response}'}</div>
              </div>
            )}

            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">Model *</label>
                {form.provider === 'custom' ? (
                  <input className="form-input" value={form.model} onChange={set('model')}
                    placeholder="model-name" />
                ) : (
                  <select className="form-select" value={form.model} onChange={set('model')}>
                    {(PROVIDER_MODELS[form.provider] ?? []).map(m =>
                      <option key={m} value={m}>{m}</option>
                    )}
                  </select>
                )}
              </div>
              <div className="form-group">
                <label className="form-label">API Key *</label>
                <input className="form-input font-mono" type="password" value={form.api_key}
                  onChange={set('api_key')} placeholder="sk-..." required />
                <div className="form-hint">Used only for this audit. Not stored in plain text.</div>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">System Prompt Hint (optional)</label>
              <textarea className="form-textarea" value={form.system_prompt_hint}
                onChange={set('system_prompt_hint')}
                placeholder="If you know the system prompt, paste it here to improve analysis accuracy…" />
              <div className="form-hint">Helps the analyzer better evaluate whether leakage occurred.</div>
            </div>

            <div className="flex" style={{ justifyContent: 'flex-end', marginTop: 8 }}>
              <button type="button" className="btn btn-primary" onClick={() => setStep(2)}>
                Next: Scan Options →
              </button>
            </div>
          </div>
        )}

        {/* ── Step 2: Scan Options ─────────────────────────────────── */}
        {step === 2 && (
          <div className="card">
            <h3 style={{ marginBottom: 8 }}>Step 2: Select Scan Categories</h3>
            <p className="text-muted text-sm mb-24">
              {totalTests} tests will be executed across {form.scan_categories.length} categories.
            </p>

            <div className="checkbox-grid mb-24">
              {SCAN_CATEGORIES.map(cat => {
                const checked = form.scan_categories.includes(cat.id)
                return (
                  <label key={cat.id} className={`checkbox-item${checked ? ' checked' : ''}`}
                    onClick={() => toggleCategory(cat.id)}>
                    <div className="checkbox-box">{checked ? '✓' : ''}</div>
                    <div className="checkbox-label">
                      <strong>{cat.icon} {cat.label}</strong>
                      <span>{cat.desc}</span>
                    </div>
                  </label>
                )
              })}
            </div>

            <div className="alert alert-warning">
              ⚠ These tests send adversarial prompts to your target LLM. Ensure you have authorization
              to test the target system.
            </div>

            <div className="flex gap-12" style={{ justifyContent: 'flex-end', marginTop: 16 }}>
              <button type="button" className="btn btn-ghost" onClick={() => setStep(1)}>← Back</button>
              <button type="button" className="btn btn-primary" onClick={() => setStep(3)}
                disabled={form.scan_categories.length === 0}>
                Next: Review & Launch →
              </button>
            </div>
          </div>
        )}

        {/* ── Step 3: Review & Launch ──────────────────────────────── */}
        {step === 3 && (
          <div className="card">
            <h3 style={{ marginBottom: 24 }}>Step 3: Review & Launch</h3>

            <div style={{ display: 'grid', gap: 12, marginBottom: 24 }}>
              {[
                ['Client', form.company_name],
                ['Provider', form.provider.toUpperCase()],
                ['Model', form.model],
                ['Endpoint', form.url || `Default ${form.provider} API`],
                ['Categories', `${form.scan_categories.length} / ${SCAN_CATEGORIES.length}`],
                ['Total Tests', `${totalTests} adversarial probes`],
                ['Reviewer', 'Rahul Singh'],
              ].map(([label, value]) => (
                <div key={label} className="flex-between" style={{
                  padding: '10px 16px',
                  background: 'var(--bg-overlay)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border)',
                }}>
                  <span className="text-muted text-sm">{label}</span>
                  <span className="font-bold text-sm">{value}</span>
                </div>
              ))}
            </div>

            <div className="alert alert-info mb-24">
              ℹ The audit will run in the background. You will see real-time progress on the results page.
            </div>

            <div className="flex gap-12" style={{ justifyContent: 'flex-end' }}>
              <button type="button" className="btn btn-ghost" onClick={() => setStep(2)}>← Back</button>
              <button type="submit" className="btn btn-danger btn-lg" disabled={loading}>
                {loading ? <><span className="spinner" /> Launching…</> : '🚀 Launch Audit'}
              </button>
            </div>
          </div>
        )}
      </form>
    </div>
  )
}
