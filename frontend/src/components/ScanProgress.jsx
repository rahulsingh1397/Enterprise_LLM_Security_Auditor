/**
 * Real-time scan progress panel — connects to WebSocket.
 */
import { useEffect, useRef, useState } from 'react'
import { connectProgressWs } from '../services/api'

export default function ScanProgress({ auditId, onComplete }) {
  const [events, setEvents]   = useState([])
  const [progress, setProgress] = useState({ completed: 0, total: 0, percent: 0, scanner: '' })
  const [done, setDone]       = useState(false)
  const [error, setError]     = useState(null)
  const logRef = useRef(null)

  useEffect(() => {
    if (!auditId) return
    const ws = connectProgressWs(
      auditId,
      (msg) => {
        if (msg.event === 'progress') {
          setProgress({ completed: msg.completed, total: msg.total, percent: msg.percent, scanner: msg.scanner })
          setEvents((prev) => {
            const next = [...prev, msg]
            return next.slice(-80) // keep last 80
          })
        } else if (msg.event === 'completed') {
          setProgress({ completed: msg.total, total: msg.total, percent: 100, scanner: 'Complete' })
          setDone(true)
          setEvents((prev) => [...prev, msg])
          onComplete?.()
        } else if (msg.event === 'error') {
          setError(msg.message)
        }
      },
      () => setError('Connection lost')
    )
    return () => ws.close()
  }, [auditId])

  // Auto-scroll log
  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
  }, [events])

  return (
    <div className="card">
      {/* Header */}
      <div className="flex-between mb-16">
        <div>
          <h3 style={{ marginBottom: 4 }}>
            {done ? '✅ Scan Complete' : error ? '❌ Scan Error' : '🔍 Scanning…'}
          </h3>
          <div className="text-muted text-sm">
            {progress.scanner && !done && `Running: ${progress.scanner}`}
            {done && 'All tests finished'}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: done ? 'var(--green)' : 'var(--blue)' }}>
            {progress.percent}%
          </div>
          <div className="text-dim text-xs">{progress.completed} / {progress.total} tests</div>
        </div>
      </div>

      {/* Progress bar */}
      <div className="progress-bar-bg mb-16">
        <div
          className="progress-bar-fill"
          style={{
            width: `${progress.percent}%`,
            background: done ? 'var(--green)' : 'linear-gradient(90deg, var(--blue), var(--purple))',
          }}
        />
      </div>

      {error && (
        <div className="alert alert-error mb-16">{error}</div>
      )}

      {/* Live log */}
      <div
        ref={logRef}
        style={{
          background: 'var(--bg-overlay)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-sm)',
          padding: '12px 14px',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.78rem',
          color: 'var(--text-muted)',
          height: 240,
          overflowY: 'auto',
          lineHeight: 1.7,
        }}
      >
        {events.length === 0 && (
          <div style={{ color: 'var(--text-dim)' }}>Waiting for scan events…</div>
        )}
        {events.map((e, i) => (
          <div key={i} style={{ display: 'flex', gap: 12, alignItems: 'baseline' }}>
            <span style={{ color: 'var(--text-dim)', flexShrink: 0, fontSize: '0.7rem' }}>
              {String(i + 1).padStart(3, '0')}
            </span>
            <span>
              {e.event === 'completed' ? (
                <span style={{ color: 'var(--green)' }}>✓ {e.message}</span>
              ) : e.latest_finding ? (
                <span>
                  <span style={{ color: 'var(--red)' }}>⚠ VULN </span>
                  <span style={{ color: 'var(--text)' }}>{e.latest_finding.attack_name}</span>
                  <span style={{ color: 'var(--yellow)', marginLeft: 8 }}>
                    [{e.latest_finding.severity?.toUpperCase()}]
                  </span>
                </span>
              ) : (
                <span>
                  <span style={{ color: 'var(--green)' }}>✓ SAFE </span>
                  <span>{e.message?.replace('Tested: ', '')}</span>
                </span>
              )}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
