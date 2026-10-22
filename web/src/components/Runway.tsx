// Signature view: the date each product runs out at expected demand, on a calendar that
// starts at the stock date. The shaded span is where the run-out should fall (3–4 weeks for
// perishables, 6–14 otherwise). Rows group by what the rules suggest; each opens its evidence.
import { useApp } from '../ctx'
import type { Rec } from '../api'
import { fmt } from '../format'

const SPAN = 16 // weeks shown
const DAY = 86400000
const x = (w: number) => (Math.min(Math.max(w, 0), SPAN) / SPAN) * 100

const shortDate = (d: Date) => d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })

export function runOut(rec: Rec, from: string): Date | null {
  if (rec.cover_is_infinite || rec.weeks_of_cover === null) return null
  return new Date(new Date(`${from}T00:00:00`).getTime() + rec.weeks_of_cover * 7 * DAY)
}

function monthTicks(from: string) {
  const start = new Date(`${from}T00:00:00`)
  const ticks: { w: number; label: string; today?: boolean }[] = [{ w: 0, label: shortDate(start), today: true }]
  const d = new Date(start.getFullYear(), start.getMonth() + 1, 1)
  while ((d.getTime() - start.getTime()) / (7 * DAY) <= SPAN) {
    ticks.push({ w: (d.getTime() - start.getTime()) / (7 * DAY), label: d.toLocaleDateString('en-GB', { month: 'short' }) })
    d.setMonth(d.getMonth() + 1)
  }
  return ticks
}

export function RunwayCalendar() {
  const { state, openSku } = useApp()
  const m = state.meta
  const t = m.thresholds
  const ticks = monthTicks(m.analysis_date)
  const done = (r: Rec) => !r.status.startsWith('Pending')
  const byCover = (a: Rec, b: Rec) => (a.cover_is_infinite ? 1e9 : a.weeks_of_cover ?? -1) - (b.cover_is_infinite ? 1e9 : b.weeks_of_cover ?? -1)
  const recs = [...state.recommendations].sort(byCover)

  const groups: { label: string; cls: string; rows: Rec[] }[] = [
    { label: 'Reorder', cls: 'short', rows: recs.filter(r => m.reorder_actions.includes(r.action)) },
    { label: 'Raghav decides', cls: '', rows: recs.filter(r => r.action === m.review_action) },
    { label: 'Pause', cls: 'over', rows: recs.filter(r => r.action === 'Pause next order') },
    { label: 'On track', cls: '', rows: recs.filter(r => r.action === 'No action') },
  ].filter(g => g.rows.length)

  const note = (r: Rec) => {
    const perish = !!r.is_perishable
    if (m.reorder_actions.includes(r.action))
      return (
        <>
          <b>Reorder {r.recommended_qty ? fmt(r.recommended_qty) : ''}</b>
          {r.needs_review ? <> &nbsp;if Raghav agrees</> : null}
        </>
      )
    if (r.action === m.review_action) return <b>Rules disagree</b>
    if (r.action === 'Pause next order') {
      const w = r.weeks_of_cover ?? 0
      return (
        <>
          <b>Pause</b> &nbsp;
          {perish ? `over the ${t.perishable_max}-week limit` : w >= 17 ? `${Math.round(w / 4.33)} months of stock` : `over ${t.overstock} weeks`}
        </>
      )
    }
    return <>no change</>
  }

  return (
    <div className="runway">
      <div className="axis" aria-hidden="true">
        <span />
        <div className="ticks">
          {ticks.map(k => (
            <span key={k.label} className={k.today ? 'today' : undefined} style={{ left: `${x(k.w)}%` }}>
              {k.label}
            </span>
          ))}
        </div>
        <span />
      </div>
      {groups.map(g => (
        <div key={g.label}>
          <div className="group">
            <span className="sc">
              <b>{g.label}</b> · {g.rows.length}
            </span>
            <span />
            <span />
          </div>
          {g.rows.map(r => {
            const perish = !!r.is_perishable
            const [lo, hi] = perish ? [t.perishable_min, t.perishable_max] : [t.stockout, t.overstock]
            const w = r.cover_is_infinite ? SPAN + 1 : r.weeks_of_cover ?? 0
            const end = runOut(r, m.analysis_date)
            const label = end ? shortDate(end) : 'no recent sales'
            const beyond = w > SPAN
            return (
              <button
                key={r.sku_id}
                type="button"
                className={`rrow ${g.cls} ${r.needs_review ? 'flag' : ''}`}
                onClick={() => openSku(r.sku_id)}
                aria-label={`${r.sku_name.replace('Freshroots ', '')}: runs out ${label}. ${r.action}. Open the evidence.`}
              >
                <span className="name">
                  {r.sku_name.replace('Freshroots ', '')}
                  {perish && <small>perishable</small>}
                </span>
                <span className="track" aria-hidden="true">
                  <span className="grid-lines">
                    {ticks.slice(1).map(k => (
                      <i key={k.label} style={{ left: `${x(k.w)}%` }} />
                    ))}
                  </span>
                  <span className="band" style={{ left: `${x(lo)}%`, width: `${x(hi) - x(lo)}%` }} />
                  <span className="line" style={{ width: `${x(w)}%` }} />
                  {beyond ? (
                    <>
                      <span className="beyond" />
                      <span className="date in num" style={{ left: '100%' }}>
                        {label} →
                      </span>
                    </>
                  ) : (
                    <>
                      <span className="end" style={{ left: `calc(${x(w)}% - 1px)` }} />
                      <span className="date num" style={{ left: `${x(w)}%` }}>
                        {label}
                      </span>
                    </>
                  )}
                </span>
                <span className="note">
                  {note(r)}
                  {done(r) && <span className="status-done">{r.status}</span>}
                </span>
              </button>
            )
          })}
        </div>
      ))}
      <div className="legend">
        <span>
          <i style={{ background: 'var(--brick)' }} />
          Runs out before its span: reorder
        </span>
        <span>
          <i style={{ background: 'var(--ochre-dot)' }} />
          Lasts past its span: pause
        </span>
        <span>
          <i style={{ background: 'var(--ink-2)' }} />
          On track
        </span>
        <span>
          <i className="box" style={{ background: 'var(--paper-3)', border: '1px dashed var(--faint)' }} />
          Where it should run out
        </span>
      </div>
    </div>
  )
}
