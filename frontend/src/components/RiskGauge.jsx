/**
 * Semi-circular risk gauge SVG component.
 * score: 0-100, higher = more vulnerable
 */
export default function RiskGauge({ score = 0, level = 'Minimal', size = 200 }) {
  const COLORS = {
    Critical: '#f85149',
    High:     '#d29922',
    Medium:   '#388bfd',
    Low:      '#3fb950',
    Minimal:  '#3fb950',
  }
  const color = COLORS[level] ?? '#8b949e'

  // Arc math: 0 score = left end, 100 = right end
  const r = 70
  const cx = 90
  const cy = 85
  const totalDeg = 180
  const sweepDeg = (score / 100) * totalDeg

  // Convert polar to cartesian
  const toXY = (deg) => {
    const rad = ((deg - 180) * Math.PI) / 180
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
  }

  const start = toXY(0)
  const end = toXY(sweepDeg)
  const largeArc = sweepDeg > 90 ? 1 : 0

  const trackStart = toXY(0)
  const trackEnd = toXY(180)

  return (
    <div className="risk-gauge-wrap">
      <svg width={size} height={size * 0.6} viewBox="0 0 180 110">
        {/* Background track */}
        <path
          d={`M ${trackStart.x} ${trackStart.y} A ${r} ${r} 0 0 1 ${trackEnd.x} ${trackEnd.y}`}
          fill="none" stroke="var(--bg-overlay)" strokeWidth="12" strokeLinecap="round"
        />
        {/* Score arc */}
        {score > 0 && (
          <path
            d={`M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 1 ${end.x} ${end.y}`}
            fill="none" stroke={color} strokeWidth="12" strokeLinecap="round"
          />
        )}
        {/* Zone labels */}
        <text x="16" y="100" fontSize="8" fill="#3fb950" fontWeight="600">Low</text>
        <text x="82" y="16" fontSize="8" fill="#d29922" fontWeight="600" textAnchor="middle">Med</text>
        <text x="160" y="100" fontSize="8" fill="#f85149" fontWeight="600" textAnchor="end">High</text>
      </svg>

      <div style={{ textAlign: 'center', marginTop: -8 }}>
        <div style={{ fontSize: '2.4rem', fontWeight: 800, color, lineHeight: 1 }}>
          {score}
        </div>
        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 2 }}>/ 100</div>
        <div style={{
          display: 'inline-block',
          marginTop: 6,
          padding: '3px 12px',
          borderRadius: 20,
          background: `${color}18`,
          border: `1px solid ${color}55`,
          color,
          fontSize: '0.75rem',
          fontWeight: 700,
        }}>
          {level} Risk
        </div>
      </div>
    </div>
  )
}
