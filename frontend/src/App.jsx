import { Routes, Route, NavLink } from 'react-router-dom'
import Home from './pages/Home'
import NewAudit from './pages/NewAudit'
import AuditResults from './pages/AuditResults'
import History from './pages/History'
import Templates from './pages/Templates'
import Login from './pages/Login'
import { AuthProvider } from './hooks/useAuth'
import ThemeToggle from './components/ThemeToggle'

const NAV = [
  { to: '/',           icon: '📊', label: 'Dashboard' },
  { to: '/audit/new',  icon: '🚀', label: 'New Audit' },
  { to: '/templates',  icon: '📁', label: 'Templates' },
  { to: '/history',    icon: '📋', label: 'Audit History' },
]

export default function App() {
  return (
    <AuthProvider>
      <div className="app-shell">
        <aside className="sidebar">
          <div className="sidebar-logo">
            <div className="sidebar-logo-icon">🛡️</div>
            <h1>Enterprise LLM<br/>Security Auditor</h1>
            <p>v1.1 · by Rahul Singh</p>
          </div>

          <nav className="sidebar-nav">
            <div className="nav-section-label">Navigation</div>
            {NAV.map(({ to, icon, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
              >
                <span className="nav-icon">{icon}</span>
                {label}
              </NavLink>
            ))}
          </nav>

          <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border)', fontSize: '0.72rem', color: 'var(--text-dim)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <span style={{ fontWeight: 700, color: 'var(--text-muted)' }}>Theme</span>
              <ThemeToggle />
            </div>
            <div style={{ fontWeight: 700, color: 'var(--text-muted)', marginBottom: 4 }}>Reviewer</div>
            <div>Rahul Singh</div>
            <div style={{ marginTop: 8, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 4 }}>Powered by</div>
            <div>Claude claude-sonnet-4-6</div>
          </div>
        </aside>

        <main className="main-content">
          <Routes>
            <Route path="/"             element={<Home />} />
            <Route path="/audit/new"    element={<NewAudit />} />
            <Route path="/audit/:id"    element={<AuditResults />} />
            <Route path="/history"      element={<History />} />
            <Route path="/templates"    element={<Templates />} />
            <Route path="/login"        element={<Login />} />
          </Routes>
        </main>
      </div>
    </AuthProvider>
  )
}
