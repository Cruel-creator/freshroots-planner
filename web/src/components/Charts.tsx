// Data-drawn SVG charts. Lines draw on when they enter the viewport.
// On phones each chart switches to a narrow viewBox so type stays legible.
import { useEffect, useMemo, useRef, useState } from 'react'
import { scaleBand, scaleLinear, scalePoint } from 'd3-scale'
import { area, curveMonotoneX, line } from 'd3-shape'
import { max, min } from 'd3-array'
import gsap from 'gsap'
import { useGSAP } from '@gsap/react'
import { prefersReducedMotion } from '../motion'
import type { Weekly } from '../api'

const INK = '#334155'
const BRAND = '#15803d'
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

function useDrawOn(scope: React.RefObject<SVGSVGElement | null>, deps: unknown[] = []) {
  useGSAP(
    () => {
      const svg = scope.current
      if (!svg || prefersReducedMotion()) return
      svg.querySelectorAll<SVGPathElement>('[data-draw]').forEach(p => {
        const len = p.getTotalLength()
        gsap.fromTo(
          p,
          { strokeDasharray: len, strokeDashoffset: len },
          { strokeDashoffset: 0, duration: 1.8, ease: 'expo.out', scrollTrigger: { trigger: svg, start: 'top 85%', once: true } },
        )
      })
      const grow = svg.querySelectorAll<SVGRectElement>('[data-grow]')
      if (grow.length)
        gsap.from(grow, {
          scaleY: 0,
          transformOrigin: '50% 100%',
          duration: 1.1,
          ease: 'expo.out',
          stagger: 0.025,
          scrollTrigger: { trigger: svg, start: 'top 85%', once: true },
        })
      const fade = svg.querySelectorAll('[data-fade]')
      if (fade.length) gsap.from(fade, { autoAlpha: 0, duration: 0.8, delay: 0.6, scrollTrigger: { trigger: svg, start: 'top 85%', once: true } })
    },
    { scope, dependencies: deps, revertOnUpdate: true },
  )
}

/** Total weekly units across SKUs, festival-month weeks shaded. Domain fitted to the data. */
export function SalesChart({ weekly }: { weekly: Weekly[] }) {
  const ref = useRef<SVGSVGElement>(null)
  const narrow = useNarrow()
  const W = narrow ? 420 : 960
  const H = narrow ? 260 : 400
  const m = { t: 24, r: narrow ? 10 : 16, b: 34, l: narrow ? 44 : 52 }
  const rows = useMemo(() => {
    const by = new Map<string, { week: string; units: number; festival: boolean }>()
    weekly.forEach(w => {
      const cur = by.get(w.week) || { week: w.week, units: 0, festival: !!w.is_festival }
      cur.units += w.units
      by.set(w.week, cur)
    })
    return [...by.values()].sort((a, b) => a.week.localeCompare(b.week))
  }, [weekly])
  const x = scalePoint<string>().domain(rows.map(r => r.week)).range([m.l, W - m.r]).padding(0.3)
  const lo = min(rows, r => r.units) ?? 0
  const hi = max(rows, r => r.units) ?? 1
  const pad = Math.max(20, (hi - lo) * 0.35)
  const y = scaleLinear().domain([lo - pad, hi + pad]).nice(4).range([H - m.b, m.t])
  const step = x.step()
  const path = line<(typeof rows)[number]>().x(r => x(r.week)!).y(r => y(r.units)).curve(curveMonotoneX)(rows) || ''
  const fill = area<(typeof rows)[number]>().x(r => x(r.week)!).y0(H - m.b).y1(r => y(r.units)).curve(curveMonotoneX)(rows) || ''
  useDrawOn(ref, [rows.length, narrow])
  const last = rows[rows.length - 1]
  const every = narrow ? 3 : 2
  return (
    <svg ref={ref} className={`chart ${narrow ? 'narrow' : ''}`} viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Weekly units sold across all SKUs">
      {rows.map(r =>
        r.festival ? <rect key={`f-${r.week}`} x={x(r.week)! - step / 2} y={m.t} width={step} height={H - m.b - m.t} fill="rgba(217,119,6,0.08)" /> : null,
      )}
      {y.ticks(4).map(t => (
        <g key={t}>
          <line x1={m.l} x2={W - m.r} y1={y(t)} y2={y(t)} stroke="#e8e8ed" />
          <text x={m.l - 10} y={y(t) + 4} textAnchor="end">
            {t.toLocaleString('en-IN')}
          </text>
        </g>
      ))}
      <path d={fill} fill="rgba(21,128,61,0.07)" data-fade />
      <path d={path} fill="none" stroke={BRAND} strokeWidth={2.2} strokeLinecap="round" data-draw />
      {rows.map((r, i) =>
        (rows.length - 1 - i) % every === 0 ? (
          <text key={`x-${r.week}`} x={x(r.week)} y={H - 10} textAnchor="middle">
            {short(r.week)}
          </text>
        ) : null,
      )}
      {last && <circle cx={x(last.week)} cy={y(last.units)} r={4.5} fill={BRAND} stroke="#fff" strokeWidth={2} data-fade />}
    </svg>
  )
}

/** One SKU: weekly bars, trailing 12-week baseline, festival-adjusted demand used for cover. */
export function SkuChart({ weekly, adjusted, window, compact = false }: { weekly: Weekly[]; adjusted: number | null; window: string[]; compact?: boolean }) {
  const ref = useRef<SVGSVGElement>(null)
  const narrowViewport = useNarrow()
  const narrow = compact || narrowViewport
  const W = narrow ? 420 : 960
  const H = narrow ? 240 : 260
  const m = { t: 22, r: 10, b: 30, l: 40 }
  const rows = useMemo(() => [...weekly].sort((a, b) => a.week.localeCompare(b.week)), [weekly])
  const trailing = rows.map((_, i) => (i >= 11 ? rows.slice(i - 11, i + 1).reduce((s, r) => s + r.units, 0) / 12 : null))
  const x = scaleBand<string>().domain(rows.map(r => r.week)).range([m.l, W - m.r]).padding(0.28)
  const yMax = Math.max(max(rows, r => r.units) ?? 1, adjusted ?? 0) * 1.15
  const y = scaleLinear().domain([0, yMax]).nice(4).range([H - m.b, m.t])
  const recent = new Set(window.slice(-4))
  const pts = rows.map((r, i) => ({ x: x(r.week)! + x.bandwidth() / 2, y: trailing[i] })).filter(p => p.y !== null) as { x: number; y: number }[]
  const base = line<{ x: number; y: number }>().x(p => p.x).y(p => y(p.y)).curve(curveMonotoneX)(pts) || ''
  useDrawOn(ref, [rows.length, adjusted, narrow])
  return (
    <svg ref={ref} className={`chart ${narrow ? 'narrow' : ''}`} viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Weekly units with 12-week baseline">
      {y.ticks(4).map(t => (
        <g key={t}>
          <line x1={m.l} x2={W - m.r} y1={y(t)} y2={y(t)} stroke="#e8e8ed" />
          <text x={m.l - 8} y={y(t) + 4} textAnchor="end">
            {t}
          </text>
        </g>
      ))}
      {rows.map(r => (
        <rect
          key={r.week}
          data-grow
          x={x(r.week)}
          y={y(r.units)}
          width={x.bandwidth()}
          height={H - m.b - y(r.units)}
          rx={narrow ? 2 : 4}
          fill={recent.has(r.week) ? INK : r.is_festival ? '#8fd3a1' : '#d2d2d7'}
        >
          <title>
            {r.week}: {r.units} units{r.is_festival ? ' (festival month)' : ''}
          </title>
        </rect>
      ))}
      <path d={base} fill="none" stroke="#ff9f0a" strokeWidth={2.2} data-draw />
      {adjusted !== null && (
        <g data-fade>
          <line x1={m.l} x2={W - m.r} y1={y(adjusted)} y2={y(adjusted)} stroke="#a34a00" strokeWidth={1.4} strokeDasharray="6 5" />
          <text x={W - m.r} y={y(adjusted) - 7} textAnchor="end" style={{ fill: '#a34a00', fontWeight: 600 }}>
            {adjusted.toFixed(1)} / wk used for cover
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

/** Grouped columns: WAPE per target week, per method. */
export function WeekColumns({ data, methods, colors }: { data: { target: string; method: string; WAPE: number; target_festival: boolean }[]; methods: string[]; colors: Record<string, string> }) {
  const ref = useRef<SVGSVGElement>(null)
  const narrow = useNarrow()
  const W = narrow ? 420 : 960
  const H = narrow ? 280 : 300
  const m = { t: 20, r: 8, b: 46, l: 40 }
  const weeks = [...new Set(data.map(d => d.target))].sort()
  const x0 = scaleBand<string>().domain(weeks).range([m.l, W - m.r]).paddingInner(narrow ? 0.2 : 0.3).paddingOuter(0.06)
  const x1 = scaleBand<string>().domain(methods).range([0, x0.bandwidth()]).padding(0.12)
  const y = scaleLinear().domain([0, (max(data, d => d.WAPE) ?? 0.2) * 1.15]).nice(4).range([H - m.b, m.t])
  useDrawOn(ref, [data.length, narrow])
  return (
    <svg ref={ref} className={`chart ${narrow ? 'narrow' : ''}`} viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Forecast error by target week">
      {y.ticks(4).map(t => (
        <g key={t}>
          <line x1={m.l} x2={W - m.r} y1={y(t)} y2={y(t)} stroke="#e8e8ed" />
          <text x={m.l - 8} y={y(t) + 4} textAnchor="end">
            {Math.round(t * 100)}%
          </text>
        </g>
      ))}
      {weeks.map(w => {
        const fest = data.find(d => d.target === w)?.target_festival
        return (
          <g key={w} transform={`translate(${x0(w)},0)`}>
            {methods.map(meth => {
              const d = data.find(r => r.target === w && r.method === meth)
              if (!d) return null
              return (
                <rect key={meth} data-grow x={x1(meth)} y={y(d.WAPE)} width={x1.bandwidth()} height={H - m.b - y(d.WAPE)} rx={narrow ? 2 : 4} fill={colors[meth] || '#86868b'}>
                  <title>
                    {w} · {meth}: {(d.WAPE * 100).toFixed(1)}%
                  </title>
                </rect>
              )
            })}
            <text x={x0.bandwidth() / 2} y={H - 26} textAnchor="middle">
              {short(w)}
            </text>
            <text x={x0.bandwidth() / 2} y={H - 9} textAnchor="middle" style={{ fill: fest ? '#1d7a35' : '#6e6e73' }}>
              {fest ? 'festival' : 'regular'}
            </text>
          </g>
        )
      })}
    </svg>
  )
}

/** Donut for a small categorical mix; segments sweep in once. */
export function Donut({ data, size = 180, label, sub }: { data: { label: string; value: number; color: string }[]; size?: number; label: string; sub: string }) {
  const ref = useRef<SVGSVGElement>(null)
  const total = data.reduce((s, d) => s + d.value, 0) || 1
  const r = size / 2 - 14
  const c = 2 * Math.PI * r
  let acc = 0
  useGSAP(
    () => {
      if (!ref.current || prefersReducedMotion()) return
      gsap.from(ref.current.querySelectorAll('circle[data-seg]'), {
        strokeDasharray: `0 ${c}`,
        duration: 1.1,
        ease: 'expo.out',
        stagger: 0.08,
        scrollTrigger: { trigger: ref.current, start: 'top 90%', once: true },
      })
    },
    { scope: ref, dependencies: [total] },
  )
  return (
    <svg ref={ref} viewBox={`0 0 ${size} ${size}`} width="100%" style={{ maxWidth: size, display: 'block' }} role="img" aria-label={`${label}: ${data.map(d => `${d.value} ${d.label}`).join(', ')}`}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#f0f1f3" strokeWidth={20} />
      {data.map(d => {
        const len = (d.value / total) * c
        const seg = (
          <circle
            key={d.label}
            data-seg
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={d.color}
            strokeWidth={20}
            strokeDasharray={`${Math.max(0, len - 2)} ${c}`}
            strokeDashoffset={-acc}
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
          />
        )
        acc += len
        return d.value ? seg : null
      })}
      <text x="50%" y="47%" textAnchor="middle" style={{ fontSize: 30, fontWeight: 650, fill: '#111827', fontFamily: 'var(--font)' }}>
        {label}
      </text>
      <text x="50%" y="61%" textAnchor="middle" style={{ fontSize: 12, fill: '#6b7280', fontFamily: 'var(--font)' }}>
        {sub}
      </text>
    </svg>
  )
}

/** Compact week strip: one cell per week per SKU that raised a signal. */
export function SignalStrip({ weeks, signals, skus }: { weeks: string[]; signals: { week: string; sku_id: string; signal_type: string; change_pct: number }[]; skus: string[] }) {
  const narrow = useNarrow()
  const W = narrow ? 420 : 960
  const row = 26
  const m = { t: 6, r: 8, b: 26, l: 64 }
  const H = m.t + skus.length * row + m.b
  const x = scaleBand<string>().domain(weeks).range([m.l, W - m.r]).padding(0.14)
  const color: Record<string, string> = { DROP_VS_TREND: '#dc2626', DROP_WEEK_ON_WEEK: '#d97706', SPIKE_VS_TREND: INK }
  return (
    <svg className={`chart ${narrow ? 'narrow' : ''}`} viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Signals detected by week and SKU">
      {skus.map((s, i) => (
        <g key={s}>
          <text x={m.l - 10} y={m.t + i * row + row / 2 + 4} textAnchor="end">
            {s}
          </text>
          {weeks.map(w => {
            const sg = signals.find(z => z.sku_id === s && z.week === w)
            return (
              <rect key={w} x={x(w)} y={m.t + i * row + 3} width={x.bandwidth()} height={row - 6} rx={4} fill={sg ? color[sg.signal_type] || '#86868b' : '#ececf0'}>
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
