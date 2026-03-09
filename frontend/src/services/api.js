const BASE = '/api'

function _authHeaders() {
  const token = localStorage.getItem('llm_audit_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ..._authHeaders(), ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  if (res.status === 204) return null
  return res.json()
}

// ── Audits ────────────────────────────────────────────────────────
export const api = {
  createAudit: (data) =>
    request('/audits', { method: 'POST', body: JSON.stringify(data) }),

  listAudits: (skip = 0, limit = 20) =>
    request(`/audits?skip=${skip}&limit=${limit}`),

  getAudit: (id) => request(`/audits/${id}`),

  getFindings: (id, vulnerableOnly = false) =>
    request(`/audits/${id}/findings?vulnerable_only=${vulnerableOnly}`),

  deleteAudit: (id) => request(`/audits/${id}`, { method: 'DELETE' }),

  getReportUrl: (id) => `${BASE}/reports/${id}/html`,

  getExportUrl: (id, format) => `${BASE}/audits/${id}/export/${format}`,

  health: () => request('/health'),

  // ── Auth ──────────────────────────────────────────────────────────
  register: (data) =>
    request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),

  login: (data) =>
    request('/auth/login', { method: 'POST', body: JSON.stringify(data) }),

  getMe: () => request('/auth/me'),

  getAuthStatus: () => request('/auth/status'),

  // ── Templates ─────────────────────────────────────────────────────
  listTemplates: () => request('/templates/'),

  getTemplate: (id) => request(`/templates/${id}`),
}

// ── WebSocket ──────────────────────────────────────────────────────
export function connectProgressWs(auditId, onMessage, onError) {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  const ws = new WebSocket(`${proto}://${location.host}/api/audits/${auditId}/progress`)

  ws.onmessage = (e) => {
    try {
      onMessage(JSON.parse(e.data))
    } catch {
      // ignore parse errors
    }
  }

  ws.onerror = (e) => onError?.(e)

  // Keep-alive ping every 30s
  const interval = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) ws.send('ping')
  }, 30000)

  ws.onclose = () => clearInterval(interval)

  return ws
}
