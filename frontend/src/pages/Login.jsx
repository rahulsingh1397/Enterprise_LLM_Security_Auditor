import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import { useAuth } from '../hooks/useAuth'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [tab, setTab] = useState('login')
  const [form, setForm] = useState({ email: '', password: '', name: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const data = tab === 'login'
        ? await api.login({ email: form.email, password: form.password })
        : await api.register({ email: form.email, password: form.password, name: form.name })
      login(data)
      navigate('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', background: 'var(--bg-primary)' }}>
      <div style={{ width: 400, background: 'var(--bg-card)', borderRadius: 12, border: '1px solid var(--border)', padding: 40 }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: 40 }}>🛡️</div>
          <h2 style={{ margin: '8px 0 4px', color: 'var(--text-primary)' }}>LLM Security Auditor</h2>
          <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>Enterprise Security Platform</p>
        </div>

        <div style={{ display: 'flex', gap: 8, marginBottom: 24, background: 'var(--bg-secondary)', borderRadius: 8, padding: 4 }}>
          {['login', 'register'].map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              style={{
                flex: 1, padding: '8px 0', border: 'none', borderRadius: 6, cursor: 'pointer',
                background: tab === t ? 'var(--accent)' : 'transparent',
                color: tab === t ? 'white' : 'var(--text-muted)',
                fontWeight: tab === t ? 700 : 400,
                transition: 'all 0.2s',
              }}
            >
              {t === 'login' ? 'Sign In' : 'Register'}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit}>
          {tab === 'register' && (
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', marginBottom: 6, color: 'var(--text-muted)', fontSize: '0.85rem' }}>Full Name</label>
              <input
                type="text" required placeholder="Rahul Singh"
                value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                style={{ width: '100%', padding: '10px 12px', background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text-primary)', fontSize: '0.9rem', boxSizing: 'border-box' }}
              />
            </div>
          )}

          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 6, color: 'var(--text-muted)', fontSize: '0.85rem' }}>Email</label>
            <input
              type="email" required placeholder="you@company.com"
              value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
              style={{ width: '100%', padding: '10px 12px', background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text-primary)', fontSize: '0.9rem', boxSizing: 'border-box' }}
            />
          </div>

          <div style={{ marginBottom: 24 }}>
            <label style={{ display: 'block', marginBottom: 6, color: 'var(--text-muted)', fontSize: '0.85rem' }}>Password</label>
            <input
              type="password" required placeholder="••••••••"
              value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
              style={{ width: '100%', padding: '10px 12px', background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text-primary)', fontSize: '0.9rem', boxSizing: 'border-box' }}
            />
          </div>

          {error && (
            <div style={{ marginBottom: 16, padding: '10px 14px', background: 'rgba(220, 53, 69, 0.1)', border: '1px solid rgba(220, 53, 69, 0.3)', borderRadius: 6, color: '#ff6b7a', fontSize: '0.85rem' }}>
              {error}
            </div>
          )}

          <button
            type="submit" disabled={loading}
            style={{ width: '100%', padding: '12px', background: 'var(--accent)', border: 'none', borderRadius: 8, color: 'white', fontSize: '0.95rem', fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1 }}
          >
            {loading ? 'Please wait...' : (tab === 'login' ? 'Sign In' : 'Create Account')}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: 20, color: 'var(--text-dim)', fontSize: '0.78rem' }}>
          {tab === 'login' ? 'First user to register becomes admin.' : 'Already have an account? Switch to Sign In.'}
        </p>
      </div>
    </div>
  )
}
