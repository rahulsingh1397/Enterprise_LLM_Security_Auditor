import { useState, useEffect } from 'react'

export default function ThemeToggle() {
  const [dark, setDark] = useState(() => {
    const stored = localStorage.getItem('theme')
    return stored ? stored === 'dark' : true  // default to dark
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }, [dark])

  return (
    <button
      onClick={() => setDark(!dark)}
      title={`Switch to ${dark ? 'light' : 'dark'} mode`}
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
        borderRadius: 8,
        padding: '6px 10px',
        cursor: 'pointer',
        fontSize: '1rem',
        lineHeight: 1,
        color: 'var(--text-muted)',
      }}
    >
      {dark ? '☀️' : '🌙'}
    </button>
  )
}
