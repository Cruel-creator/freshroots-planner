// Data-drawn SVG charts in the brief's palette: ink for the data, brick and ochre only where
// they mean something, labels written on the chart instead of legends where possible.
// On phones each chart switches to a narrow viewBox so type stays legible. No animation.
import { useEffect, useMemo, useState } from 'react'
import { scaleBand, scaleLinear, scalePoint } from 'd3-scale'
import { line } from 'd3-shape'
import { max, min } from 'd3-array'
import type { Weekly } from '../api'

export const PALETTE = {
  ink: '#1d1b17',
  ink2: '#45413a',
  muted: '#736c5c',
  faint: '#a59d8c',
  rule: '#e0d8c6',
  paper2: '#efe9dc',
  bar: '#cdc3ad',
  moss: '#3b5a2b',
  brick: '#a3412b',
  ochre: '#b8862a',
}
const short = (w: string) => w.replace(/^\d{4}-/, '')

function useNarrow() {
  const q = '(max-width: 640px)'
  const [narrow, setNarrow] = useState(() => typeof window !== 'undefined' && window.matchMedia(q).matches)
  useEffect(() => {
    const mq = window.matchMedia(q)
    const on = () => setNarrow(mq.matches)
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [])
  return narrow
}

/** Weekly totals across every product. Straight segments, festival weeks shaded, the latest week called out. */
export function SalesChart({ weekly }: { weekly: Weekly[] }) {
  const narrow = useNarrow()
  const W = narrow ? 420 : 560
  const H = narrow ? 270 : 230
  const m = { t: 34, r: narrow ? 12 : 12, b: 28, l: narrow ? 50 : 48 }
  const rows = useMemo(() => {
    const by = new Map<string, { week: string; units: number; festival: boolean; month: string }>()
    weekly.forEach(w => {
      const cur = by.get(w.week) || { week: w.week, units: 0, festival: !!w.is_festival, month: w.month }
      cur.units += w.units
      by.set(w.week, cur)
    })
    return [...by.values()].sort((a, b) => a.week.localeCompare(b.week))
  }, [weekly])
  const x = scalePoint<string>().domain(rows.map(r => r.week)).range([m.l, W - m.r]).padding(0.3)
  const lo = min(rows, r => r.units) ?? 0
  const hi = max(rows, r => r.units) ?? 1
  const pad = Math.max(20, (hi - lo) * 0.4)
  const y = scaleLinear().domain([lo - pad, hi + pad]).nice(3).range([H - m.b, m.t])
  const step = x.step()
  const path = line<(typeof rows)[number]>().x(r => x(r.week)!).y(r => y(r.units))(rows) || ''
  const last = rows[rows.length - 1]
  const fest = rows.filter(r => r.festival)
  const months = rows.filter((r, i) => i === 0 || r.month !== rows[i - 1].month)
  const monthLabel = (ym: string) => new Date(`${ym}-01T00:00:00`).toLocaleDateString('en-GB', { month: 'short' })
  return (
    <svg className={`chart ${narrow ? 'narrow' : ''}`} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Weekly units sold across all products; ${last ? `${last.units} in ${last.week}` : ''}`}>
      {fest.length > 0 && (
        <g>
          <rect x={x(fest[0].week)! - step / 2} y={m.t - 18} width={x(fest.at(-1)!.week)! - x(fest[0].week)! + step} height={H - m.b - m.t + 18} fill={PALETTE.paper2} />
          <text className="serif-label" x={x(fest[0].week)! - step / 2 + 6} y={H - m.b - 8}>
            festival month
          </text>
        </g>
      )}
      {y.ticks(3).map(t => (
        <g key={t}>
          <line x1={m.l} x2={W - m.r} y1={y(t)} y2={y(t)} stroke={PALETTE.rule} />
          <text x={m.l - 8} y={y(t) + 4} textAnchor="end">
            {t.toLocaleString('en-IN')}
          </text>
        </g>
      ))}
      <path d={path} fill="none" stroke={PALETTE.ink2} strokeWidth={1.8} strokeLinejoin="round" />
      {months.map(r => (
        <text key={`m-${r.week}`} x={x(r.week)} y={H - 8} textAnchor="middle">
          {monthLabel(r.month)}
        </text>
      ))}
      {last && (
        <g>
          <circle cx={x(last.week)} cy={y(last.units)} r={4.5} fill={PALETTE.moss} />
          <text className="callout" x={x(last.week)! - 10} y={y(last.units) - 14} textAnchor="end">
            {last.units.toLocaleString('en-IN')} this week
          </text>
        </g>
      )}
    </svg>
  )
}

/** One product: weekly units, the trailing 12-week average, and the demand used for cover. */
export function SkuChart({ weekly, adjusted, window, compact = false }: { weekly: Weekly[]; adjusted: number | null; window: string[]; compact?: boolean }) {
  const narrowViewport = useNarrow()
  const narrow = compact || narrowViewport
  const W = narrowViewport ? 420 : compact ? 620 : 960
  const H = narrowViewport ? 250 : 240
  const m = { t: 26, r: 10, b: 30, l: 40 }
  const rows = useMemo(() => [...weekly].sort((a, b) => a.week.localeCompare(b.week)), [weekly])
  const trailing = rows.map((_, i) => (i >= 11 ? rows.slice(i - 11, i + 1).reduce((s, r) => s + r.units, 0) / 12 : null))
  const x = scaleBand<string>().domain(rows.map(r => r.week)).range([m.l, W - m.r]).padding(0.3)
  const yMax = Math.max(max(rows, r => r.units) ?? 1, adjusted ?? 0) * 1.18
  const y = scaleLinear().domain([0, yMax]).nice(4).range([H - m.b, m.t])
  const recent = new Set(window.slice(-4))
  const pts = rows.map((r, i) => ({ x: x(r.week)! + x.bandwidth() / 2, y: trailing[i] })).filter(p => p.y !== null) as { x: number; y: number }[]
  const base = line<{ x: number; y: number }>().x(p => p.x).y(p => y(p.y))(pts) || ''
  const fest = rows.filter(r => r.is_festival)
  return (
    <svg className={`chart ${narrowViewport ? 'narrow' : ''}`} viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Weekly units with the 12-week average and the demand used for cover">
      {fest.length > 0 && (
        <rect x={x(fest[0].week)! - 4} y={m.t - 8} width={x(fest.at(-1)!.week)! + x.bandwidth() - x(fest[0].week)! + 8} height={H - m.b - m.t + 8} fill={PALETTE.paper2} />
      )}
      {y.ticks(4).map(t => (
        <g key={t}>
          <line x1={m.l} x2={W - m.r} y1={y(t)} y2={y(t)} stroke={PALETTE.rule} />
          <text x={m.l - 8} y={y(t) + 4} textAnchor="end">
            {t}
          </text>
        </g>
      ))}
      {rows.map(r => (
        <rect key={r.week} x={x(r.week)} y={y(r.units)} width={x.bandwidth()} height={H - m.b - y(r.units)} fill={recent.has(r.week) ? PALETTE.ink2 : PALETTE.bar}>
          <title>
            {r.week}: {r.units} units{r.is_festival ? ' (festival month)' : ''}
          </title>
        </rect>
      ))}
      <path d={base} fill="none" stroke={PALETTE.moss} strokeWidth={2} />
      {adjusted !== null && (
        <g>
          <line x1={m.l} x2={W - m.r} y1={y(adjusted)} y2={y(adjusted)} stroke={PALETTE.brick} strokeWidth={1.4} strokeDasharray="5 5" />
          <text x={W - m.r} y={y(adjusted) - 7} textAnchor="end" style={{ fill: PALETTE.brick, fontWeight: 600 }}>
            {adjusted.toFixed(1)} a week used for cover
          </text>
        </g>
      )}
      {rows.map((r, i) =>
        (rows.length - 1 - i) % (narrow ? 4 : 2) === 0 ? (
          <text key={`x-${r.week}`} x={x(r.week)! + x.bandwidth() / 2} y={H - 9} textAnchor="middle">
            {short(r.week)}
          </text>
        ) : null,
      )}
    </svg>
  )
}

/** Grouped columns: forecast error per target week, per method. */
export function WeekColumns({ data, methods, colors }: { data: { target: string; method: string; WAPE: number; target_festival: boolean }[]; methods: string[]; colors: Record<string, string> }) {
  const narrow = useNarrow()
  const W = narrow ? 420 : 960
  const H = narrow ? 280 : 300
  const m = { t: 20, r: 8, b: 46, l: 40 }
  const weeks = [...new Set(data.map(d => d.target))].sort()
  const x0 = scaleBand<string>().domain(weeks).range([m.l, W - m.r]).paddingInner(narrow ? 0.2 : 0.3).paddingOuter(0.06)
  const x1 = scaleBand<string>().domain(methods).range([0, x0.bandwidth()]).padding(0.14)
  const y = scaleLinear().domain([0, (max(data, d => d.WAPE) ?? 0.2) * 1.15]).nice(4).range([H - m.b, m.t])
  return (
    <svg className={`chart ${narrow ? 'narrow' : ''}`} viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Forecast error by target week">
      {y.ticks(4).map(t => (
        <g key={t}>
          <line x1={m.l} x2={W - m.r} y1={y(t)} y2={y(t)} stroke={PALETTE.rule} />
          <text x={m.l - 8} y={y(t) + 4} textAnchor="end">
            {Math.round(t * 100)}%
          </text>
        </g>
      ))}
      {weeks.map(w => {
        const fest = data.find(d => d.target === w)?.target_festival
        return (
          <g key={w} transform={`translate(${x0(w)},0)`}>
            {fest && <rect x={-4} y={m.t} width={x0.bandwidth() + 8} height={H - m.b - m.t} fill={PALETTE.paper2} />}
            {methods.map(meth => {
              const d = data.find(r => r.target === w && r.method === meth)
              if (!d) return null
              return (
                <rect key={meth} x={x1(meth)} y={y(d.WAPE)} width={x1.bandwidth()} height={H - m.b - y(d.WAPE)} fill={colors[meth] || PALETTE.faint}>
                  <title>
                    {w} · {meth}: {(d.WAPE * 100).toFixed(1)}%
                  </title>
                </rect>
              )
            })}
            <text x={x0.bandwidth() / 2} y={H - 26} textAnchor="middle">
              {short(w)}
            </text>
            <text x={x0.bandwidth() / 2} y={H - 9} textAnchor="middle" className={fest ? 'serif-label' : undefined}>
              {fest ? 'festival' : ''}
            </text>
          </g>
        )
      })}
    </svg>
  )
}

/** Week-by-product grid: one cell per week for each product that ever raised a sales alert. */
export function SignalStrip({ weeks, signals, skus }: { weeks: string[]; signals: { week: string; sku_id: string; signal_type: string; change_pct: number }[]; skus: string[] }) {
  const narrow = useNarrow()
  const W = narrow ? 420 : 960
  const row = 26
  const m = { t: 6, r: 8, b: 26, l: 64 }
  const H = m.t + skus.length * row + m.b
  const x = scaleBand<string>().domain(weeks).range([m.l, W - m.r]).padding(0.14)
  const color: Record<string, string> = { DROP_VS_TREND: PALETTE.brick, DROP_WEEK_ON_WEEK: PALETTE.ochre, SPIKE_VS_TREND: PALETTE.ink2 }
  return (
    <svg className={`chart ${narrow ? 'narrow' : ''}`} viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Sales alerts by week and product">
      {skus.map((s, i) => (
        <g key={s}>
          <text x={m.l - 10} y={m.t + i * row + row / 2 + 4} textAnchor="end">
            {s}
          </text>
          {weeks.map(w => {
            const sg = signals.find(z => z.sku_id === s && z.week === w)
            return (
              <rect key={w} x={x(w)} y={m.t + i * row + 3} width={x.bandwidth()} height={row - 6} rx={1} fill={sg ? color[sg.signal_type] || PALETTE.faint : '#e9e2d2'}>
                {sg && (
                  <title>
                    {s} {w}: {sg.signal_type.replaceAll('_', ' ').toLowerCase()} {(sg.change_pct * 100).toFixed(1)}%
                  </title>
                )}
              </rect>
            )
          })}
        </g>
      ))}
      {weeks.map((w, i) =>
        (weeks.length - 1 - i) % (narrow ? 4 : 2) === 0 ? (
          <text key={w} x={x(w)! + x.bandwidth() / 2} y={H - 8} textAnchor="middle">
            {short(w)}
          </text>
        ) : null,
      )}
    </svg>
  )
}
