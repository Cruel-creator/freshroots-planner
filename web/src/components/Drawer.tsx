// SKU detail: the evidence behind one recommendation, with the decision controls.
import { useEffect } from 'react'
import { X } from 'lucide-react'
import { useApp } from '../ctx'
import { cover, fmt, pct, recState, statusState } from '../format'
import { lockScroll } from '../motion'
import { SkuChart } from './Charts'
import { Decide } from './Decide'

export function SkuDrawer() {
  const { openSkuId, openSku, recBySku, state } = useApp()
  const rec = openSkuId ? recBySku.get(openSkuId) : undefined
  const open = !!rec

  useEffect(() => {
    lockScroll(open)
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && openSku(null)
    window.addEventListener('keydown', onKey)
    return () => {
      window.removeEventListener('keydown', onKey)
      lockScroll(false)
    }
  }, [open, openSku])

  const weekly = rec ? state.weekly.filter(w => w.SKU_ID === rec.sku_id) : []
  const src = rec ? weekly.filter(w => rec.source_weeks.includes(w.week)).sort((a, b) => a.week.localeCompare(b.week)) : []
  const exc = rec ? state.exceptions.filter(e => e.sku_id === rec.sku_id) : []
  const st = rec ? recState(rec) : 'ok'
  const t = state.meta.thresholds

  return (
    <>
      <div className={`scrim ${open ? 'open' : ''}`} onClick={() => openSku(null)} aria-hidden="true" />
      <aside className={`drawer ${open ? 'open' : ''}`} role="dialog" aria-modal="true" aria-label={rec ? `${rec.sku_id} details` : 'SKU details'} data-lenis-prevent>
        {rec && (
          <>
            <div className="drawer-head">
              <div>
                <div className="fine">
                  {rec.sku_id} · {rec.category} · {rec.perishability === 'High' ? 'Perishable' : 'Standard'}
                </div>
                <div className="subtitle">{rec.sku_name.replace('Freshroots ', '')}</div>
              </div>
              <button className="icon-btn" aria-label="Close" onClick={() => openSku(null)}>
                <X size={18} />
              </button>
            </div>
            <div className="drawer-body">
              <div className="figures" style={{ ['--cols' as string]: 3, marginTop: 20 }}>
                <div className="figure">
                  <span className={`figure-num md ${st === 'crit' ? 'hl-red' : st === 'warn' ? 'hl-orange' : ''}`}>{cover(rec)}</span>
                  <span className="figure-label">weeks of cover</span>
                  <span className="figure-note">
                    Target {rec.is_perishable ? `${t.perishable_min}–${t.perishable_max}` : `${t.stockout}–${t.overstock}`} weeks
                  </span>
                </div>
                <div className="figure">
                  <span className="figure-num md">{fmt(rec.adjusted_weekly_demand, 0)}</span>
                  <span className="figure-label">units a week</span>
                  <span className="figure-note">{rec.festival_uplift_applied ? 'Includes 25% festival uplift' : 'No uplift this month'}</span>
                </div>
                <div className="figure">
                  <span className="figure-num md">{rec.recommended_qty === null ? '—' : fmt(rec.recommended_qty)}</span>
                  <span className="figure-label">{rec.action}</span>
                  <span className="figure-note">{rec.qty_basis}</span>
                </div>
              </div>

              <div className="sheet" style={{ marginTop: 32, padding: 20 }}>
                <SkuChart weekly={weekly} adjusted={rec.adjusted_weekly_demand} window={state.meta.window} compact />
                <div className="legend">
                  <span>
                    <i style={{ background: '#1d1d1f' }} />
                    Last 4 weeks
                  </span>
                  <span>
                    <i style={{ background: '#8fd3a1' }} />
                    Festival-month week
                  </span>
                  <span>
                    <i style={{ background: '#ff9f0a', height: 3 }} />
                    Trailing 12-week average
                  </span>
                  <span>
                    <i style={{ background: '#a34a00', height: 2 }} />
                    Demand used for cover
                  </span>
                </div>
              </div>

              <section style={{ marginTop: 32 }} className="stack-gap">
                <div className="toolbar" style={{ marginBottom: 0 }}>
                  <h3 className="subtitle">Decision</h3>
                  <span className={`state ${statusState(rec.status)}`}>{rec.status}</span>
                </div>
                <Decide rec={rec} />
              </section>

              <section style={{ marginTop: 36 }}>
                <h3 className="subtitle">Why</h3>
                <p className="small" style={{ marginTop: 10 }}>
                  {rec.explanation}
                </p>
                {rec.conflicts.length > 0 && (
                  <p className="small" style={{ color: 'var(--orange-ink)' }}>
                    {rec.conflicts.join(' ')}
                  </p>
                )}
                {exc.map(e => (
                  <p key={e.code} className="small">
                    <strong>{e.category}.</strong> {e.signal}. {e.why_not_automated} <span className="muted">Next: {e.suggested_action}</span>
                  </p>
                ))}
              </section>

              <details className="disclose" style={{ marginTop: 20 }}>
                <summary>Formulas</summary>
                <div>
                  <ul className="formula">
                    <li>
                      4-week average <code>{fmt(rec.recent_4w_avg, 1)}</code> = units in {rec.source_weeks.at(-4)}–{rec.source_weeks.at(-1)} ÷ 4
                    </li>
                    <li>
                      12-week average <code>{fmt(rec.baseline_12w_avg, 1)}</code> = units in {rec.source_weeks[0]}–{rec.source_weeks.at(-1)} ÷ 12
                    </li>
                    <li>
                      Demand change <code>{pct(rec.demand_change_pct)}</code> = 4-week ÷ 12-week − 1. High demand when above {Math.round(t.high_demand * 100)}%.
                    </li>
                    <li>
                      Adjusted demand <code>{fmt(rec.adjusted_weekly_demand, 1)}</code> = 12-week average × {rec.festival_uplift_applied ? (1 + t.uplift).toFixed(2) : '1.00'} ({rec.planning_month})
                    </li>
                    <li>
                      Weeks of cover <code>{cover(rec)}</code> = stock {fmt(rec.current_stock)} ÷ adjusted demand
                    </li>
                    <li>
                      Priority step applied: <code>{rec.priority_step}</code>
                    </li>
                  </ul>
                </div>
              </details>
              <details className="disclose">
                <summary>Source rows · weekly_sales.csv</summary>
                <div className="table-scroll">
                  <table className="data">
                    <thead>
                      <tr>
                        <th>Week</th>
                        <th>Month</th>
                        <th className="r">Units</th>
                      </tr>
                    </thead>
                    <tbody>
                      {src.map(w => (
                        <tr key={w.week}>
                          <td>{w.week}</td>
                          <td>
                            {w.month}
                            {w.is_festival ? <span className="sub">Festival month</span> : null}
                          </td>
                          <td className="r">{fmt(w.units)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
              <details className="disclose">
                <summary>Data quality</summary>
                <div className="small">{rec.data_quality_status}</div>
              </details>
            </div>
          </>
        )}
      </aside>
    </>
  )
}
