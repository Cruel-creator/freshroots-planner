// The brief: this week's call as a front page, the evidence that needs a person, the runway
// of run-out dates, and whether the forecast deserves trust. Every sentence is built from data.
import { useApp } from '../ctx'
import { Colophon } from '../components/Nav'
import { RunwayCalendar, runOut } from '../components/Runway'
import { SalesChart } from '../components/Charts'
import type { Exception, Rec, State } from '../api'
import { fmt, monthName, numberWord } from '../format'

const shortDate = (d: Date) => d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
const name = (r: Rec) => r.sku_name.replace('Freshroots ', '')
const list = (xs: string[]) => (xs.length <= 1 ? xs.join('') : `${xs.slice(0, -1).join(', ')} and ${xs.at(-1)}`)
const median = (xs: number[]) => {
  const s = [...xs].sort((a, b) => a - b)
  const k = Math.floor(s.length / 2)
  return s.length % 2 ? s[k] : (s[k - 1] + s[k]) / 2
}

/** A plain-language line for the exception, computed from the sales rows where possible. */
function quoteFor(e: Exception, state: State, rec?: Rec) {
  const rows = state.weekly.filter(w => w.SKU_ID === e.sku_id).sort((a, b) => a.week.localeCompare(b.week))
  const anchor = state.meta.anchor_week
  const i = rows.findIndex(w => w.week === anchor)
  if (e.code === 'UNUSUAL_LATEST_WEEK' && i >= 12 && rec) {
    const latest = rows[i].units
    const usual = median(rows.slice(i - 12, i).map(w => w.units))
    const diff = Math.round((latest / usual - 1) * 100)
    return `${name(rec)} sold ${fmt(latest)} units in week ${Number(anchor.split('-W')[1])}, ${Math.abs(diff)}% ${diff >= 0 ? 'above' : 'below'} its usual ${fmt(usual)}.`
  }
  return `${rec ? `${name(rec)}: ` : ''}${e.signal}.`
}

export function Overview() {
  const { state, openSku, recBySku } = useApp()
  const m = state.meta
  const recs = state.recommendations
  const reorders = recs.filter(r => m.reorder_actions.includes(r.action))
  const pauses = recs.filter(r => r.action === 'Pause next order')
  const review = recs.filter(r => r.needs_review || r.action === m.review_action)
  const units = reorders.reduce((s, r) => s + (r.recommended_qty ?? 0), 0)
  const withRaghav = recs.filter(r => r.status === 'Pending planner review').length
  const withProc = recs.filter(r => r.status === 'Pending procurement approval').length
  const approved = recs.filter(r => r.status === 'Procurement approved' || r.status === 'Exported as draft').length
  const firstOut = reorders.map(r => runOut(r, m.analysis_date)).filter((d): d is Date => !!d).sort((a, b) => a.getTime() - b.getTime())[0]
  const stockDay = shortDate(new Date(`${m.analysis_date}T00:00:00`))
  const week = Number(m.anchor_week.split('-W')[1])
  const word = numberWord(reorders.length).toLowerCase()

  // Demand: the last four weeks against the twelve before them.
  const weeks = [...new Set(state.weekly.map(w => w.week))].sort()
  const totals = weeks.map(w => state.weekly.filter(x => x.week === w).reduce((s, x) => s + x.units, 0))
  const avg = (xs: number[]) => xs.reduce((s, v) => s + v, 0) / (xs.length || 1)
  const last4 = avg(totals.slice(-4))
  const prior12 = avg(totals.slice(-16, -4))
  const growth = prior12 ? Math.round((last4 / prior12 - 1) * 100) : 0
  const uplift = Math.round(m.thresholds.uplift * 100)

  // Forecast check.
  const bt = Object.fromEntries(state.backtest.summary.map(s => [s.method, s]))
  const methods = [
    ['recent_4w', 'Recent 4-week average', 'reacts fastest'],
    ['baseline_12w', 'Plain 12-week average', 'the baseline'],
    ['rules_engine', 'With festival uplift', 'what the rules use'],
  ].filter(([k]) => bt[k])
  const worst = Math.max(...methods.map(([k]) => bt[k].WAPE))
  const scaleMax = Math.max(0.1, Math.ceil((worst * 100) / 10) / 10)
  const upliftLoses = bt.rules_engine && bt.baseline_12w && bt.rules_engine.WAPE > bt.baseline_12w.WAPE
  const openAlerts = state.signals.filter(s => s.status === 'New' || s.status === 'Surfaced to procurement').length

  const ex = state.exceptions[0]
  const exRec = ex ? recBySku.get(ex.sku_id) : undefined

  return (
    <main className="content">
      <div className="front">
        <div>
          <div className="sc">This week's call · stock as of {stockDay}</div>
          <h1>
            {reorders.length ? (
              <>
                Reorder {word} product{reorders.length === 1 ? '' : 's'}.{' '}
                {firstOut && (
                  <>
                    The first runs out <em>on {firstOut.toLocaleDateString('en-GB', { day: 'numeric', month: 'long' })}.</em>
                  </>
                )}
              </>
            ) : pauses.length ? (
              <>
                No reorders this week. <em>{numberWord(pauses.length)} to pause.</em>
              </>
            ) : (
              <>Every product is on track this week.</>
            )}
          </h1>
          <p className="lede">
            {reorders.length > 0 && (
              <>
                Raghav's rules suggest <b>{fmt(units)} units</b> across {reorders.length === 1 ? 'that one' : `those ${word}`}
                {pauses.length ? `, and pausing ${numberWord(pauses.length).toLowerCase()} that hold more stock than they should` : ''}.{' '}
              </>
            )}
            {m.planning_month_festival && (
              <>
                {monthName(m.planning_month).split(' ')[0]} is a festival month, so demand carries the <b>+{uplift}% uplift</b>.{' '}
              </>
            )}
            Nothing is ordered until Raghav and procurement sign each line.
          </p>
          <div className="byline num">
            {m.rule_version.replace('rules-', 'Rules ')} · {recs.length} products · sales through week {week}
          </div>
        </div>

        <aside className="docket" aria-label="On Raghav's desk">
          <div className="sc">On Raghav's desk</div>
          <ol>
            <li>
              <span className="big num">{reorders.length}</span>
              <span className="what">
                <b>Reorder</b>
                {fmt(units)} units{firstOut ? `, earliest stock-out ${shortDate(firstOut)}` : ''}
              </span>
            </li>
            <li>
              <span className="big num">{pauses.length}</span>
              <span className="what">
                <b>Pause</b>
                {pauses.length ? `${list(pauses.map(name))} ${pauses.length === 1 ? 'is' : 'are'} overstocked` : 'Nothing is overstocked'}
              </span>
            </li>
            <li>
              <span className="big num">{review.length}</span>
              <span className="what">
                <b>Needs judgment</b>
                {review.length ? `${list(review.map(name))}: the rules can't settle ${review.length === 1 ? 'it' : 'them'} alone` : 'The rules settle every line'}
              </span>
            </li>
          </ol>
          <a className="btn btn-primary cta" href="#/workbench">
            {withRaghav + withProc ? `Review ${withRaghav + withProc} open line${withRaghav + withProc === 1 ? '' : 's'}` : 'Open approvals'} <span className="arrow">→</span>
          </a>
          <div className="fine num">
            {withRaghav} with Raghav · {withProc} with procurement · {approved} approved
          </div>
        </aside>
      </div>

      {ex && (
        <div className="pull">
          <div className="mark" aria-hidden="true">
            “
          </div>
          <blockquote>
            {quoteFor(ex, state, exRec)}
            <cite>
              {ex.category} · {ex.source_data}
              {exRec?.recommended_qty ? ` · the rules suggest ${fmt(exRec.recommended_qty)} units` : ''}
            </cite>
          </blockquote>
          <aside>
            <b>Why a person decides</b>
            {ex.why_not_automated}
            <br />
            <button className="textlink" onClick={() => openSku(ex.sku_id)}>
              Open the evidence →
            </button>
          </aside>
        </div>
      )}

      <section className="s">
        <div className="shead">
          <div className="no num">01</div>
          <div>
            <h2>The runway</h2>
            <p>
              The date each product runs out at expected demand. The shaded span is where it <i>should</i> run out: {m.thresholds.stockout}–{m.thresholds.overstock} weeks from today, or {m.thresholds.perishable_min}–{m.thresholds.perishable_max} weeks for perishables. Select a product for its evidence.
            </p>
          </div>
        </div>
        <div className="indent">
          <RunwayCalendar />
        </div>
      </section>

      <section className="s">
        <div className="shead">
          <div className="no num">02</div>
          <div>
            <h2>How demand moved</h2>
            <p>Units sold each week across all {recs.length} products.</p>
          </div>
        </div>
        <div className="spread indent">
          <div>
            <SalesChart weekly={state.weekly} />
            <p className="caption">
              The last four weeks averaged {Math.abs(growth)}% {growth >= 0 ? 'more' : 'less'} than the twelve before
              {m.planning_month_festival && growth < uplift * 0.6 ? `, well short of the ${uplift}% uplift the rules assume.` : '.'}
            </p>
          </div>
          <div>
            <div className="sc">03 · Can we trust the forecast?</div>
            <p className="fine" style={{ margin: '8px 0 6px', fontSize: 14 }}>
              Average error, predicting past weeks one week ahead. Further left is better.
            </p>
            <div>
              {methods.map(([k, label, sub]) => {
                const v = bt[k].WAPE
                const left = (v / scaleMax) * 100
                return (
                  <div key={k} className={`dotrow ${v === worst ? 'worst' : ''}`}>
                    <div>
                      {label}
                      <small>{sub}</small>
                    </div>
                    <div className="dline">
                      <i style={{ left: `${left}%` }} />
                      <span className={`num ${left > 70 ? 'left' : ''}`} style={{ left: `${left}%` }}>
                        {(v * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>
            <div className="dscale">
              <span />
              <div className="num">
                <span>0%</span>
                <span>{Math.round(scaleMax * 50)}%</span>
                <span>{Math.round(scaleMax * 100)}%</span>
              </div>
            </div>
            <div className="margin-note">
              {upliftLoses ? (
                <>
                  <b>Worth raising with Raghav:</b> the plain 12-week average beat the festival uplift on past weeks. The uplift may need to vary by category.
                </>
              ) : (
                <>
                  <b>Holding up:</b> the festival uplift forecasts at least as well as the plain average on past weeks.
                </>
              )}
            </div>
            <p className="fine" style={{ marginTop: 14 }}>
              Sales alerts this week: {openAlerts ? `${openAlerts} open, holding those orders.` : 'none open, so no order is held.'}{' '}
              <a href="#/signals">Sales alerts</a> · <a href="#/backtest">Forecast detail</a>
            </p>
          </div>
        </div>
      </section>

      <Colophon />
    </main>
  )
}
