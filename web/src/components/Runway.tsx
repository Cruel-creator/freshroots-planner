// Signature chart: every SKU's weeks of cover on one axis against its own target window
// (3–4 weeks perishable, 6–14 standard). Bars grow as the card scrolls into view.
import { useRef } from 'react'
import gsap from 'gsap'
import { useGSAP } from '@gsap/react'
import { useApp } from '../ctx'
import { prefersReducedMotion } from '../motion'
import { recState } from '../format'

const MAX = 24
const COLORS = { crit: '#dc2626', warn: '#d97706', ok: '#334155', info: '#9ca3af' }

export function CoverChart() {
  const { state, openSku } = useApp()
  const t = state.meta.thresholds
  const ref = useRef<HTMLDivElement>(null)
  const rows = [...state.recommendations].sort(
    (a, b) => (a.cover_is_infinite ? 1e9 : a.weeks_of_cover ?? -1) - (b.cover_is_infinite ? 1e9 : b.weeks_of_cover ?? -1),
  )
  const pos = (w: number) => `${(Math.min(w, MAX) / MAX) * 100}%`

  useGSAP(
    () => {
      const el = ref.current
      if (!el || prefersReducedMotion()) return
      gsap.from(el.querySelectorAll('.cover-bar'), {
        scaleX: 0,
        duration: 1.1,
        ease: 'expo.out',
        stagger: 0.035,
        scrollTrigger: { trigger: el, start: 'top 88%', once: true },
      })
    },
    { scope: ref, dependencies: [rows.length] },
  )

  return (
    <div ref={ref}>
      <div role="list">
        {rows.map(r => {
          const perish = !!r.is_perishable
          const lo = perish ? t.perishable_min : t.stockout
          const hi = perish ? t.perishable_max : t.overstock
          const w = r.cover_is_infinite ? MAX : r.weeks_of_cover ?? 0
          const st = recState(r)
          return (
            <div className="cover-row" role="listitem" key={r.sku_id}>
              <button className="cover-name" onClick={() => openSku(r.sku_id)} title={`${r.sku_id} ${r.sku_name}`}>
                <b>{r.sku_id.replace('SKU', '')}</b>
                <span>{r.sku_name.replace('Freshroots ', '')}</span>
              </button>
              <div className="cover-track">
                <div className="cover-zone" style={{ left: pos(lo), width: `calc(${pos(hi)} - ${pos(lo)})` }} />
                <div className="cover-bar" style={{ width: pos(w), background: COLORS[st] }} />
              </div>
              <div className="cover-val" style={{ color: st === 'crit' ? '#b91c1c' : st === 'warn' ? '#b45309' : undefined }}>
                {r.cover_is_infinite ? '∞' : (r.weeks_of_cover ?? 0).toFixed(1)}
              </div>
            </div>
          )
        })}
      </div>
      <div className="cover-axis" aria-hidden="true">
        <div />
        <div className="cover-ticks">
          {[0, 3, 6, 10, 14, 18, 24].map(v => (
            <span key={v} style={{ left: pos(v) }}>
              {v}
            </span>
          ))}
        </div>
        <div className="fine" style={{ textAlign: 'right' }}>
          wks
        </div>
      </div>
      <div className="legend">
        <span>
          <i style={{ background: COLORS.crit }} />
          Below minimum
        </span>
        <span>
          <i style={{ background: COLORS.warn }} />
          Above maximum or high demand
        </span>
        <span>
          <i style={{ background: COLORS.ok }} />
          Within window
        </span>
        <span>
          <i style={{ background: 'rgba(22,163,74,0.25)' }} />
          Target window
        </span>
      </div>
    </div>
  )
}
