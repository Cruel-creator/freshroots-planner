import { ArrowRight } from 'lucide-react'
import { useApp } from '../ctx'
import { Card, Kpi, Page } from '../components/Nav'
import { CoverChart } from '../components/Runway'
import { Donut, SalesChart } from '../components/Charts'
import CountUp from '../components/reactbits/CountUp'
import DotGrid from '../components/reactbits/DotGrid'
import { prefersReducedMotion } from '../motion'
import { dateLong, fmt, monthName, pct, recState, statusState } from '../format'

const Num = ({ to, decimals = 0, suffix = '' }: { to: number; decimals?: number; suffix?: string }) => (
  <CountUp to={to} decimals={decimals} suffix={suffix} duration={1.2} separator="," />
)

export function Overview() {
  const { state, openSku } = useApp()
  const m = state.meta
  const recs = state.recommendations
  const reorders = recs.filter(r => m.reorder_actions.includes(r.action))
  const pauses = recs.filter(r => r.action === 'Pause next order')
  const none = recs.filter(r => r.action === 'No action')
  const decide = recs.filter(r => r.action === m.review_action)
  const review = recs.filter(r => r.needs_review || r.action === m.review_action)
  const units = reorders.reduce((s, r) => s + (r.recommended_qty ?? 0), 0)
  const withRaghav = recs.filter(r => r.status === 'Pending planner review').length
  const withProc = recs.filter(r => r.status === 'Pending procurement approval').length
  const below = recs.filter(r => recState(r) === 'crit')
  const belowPerish = below.filter(r => r.is_perishable).length

  const bt = Object.fromEntries(state.backtest.summary.map(s => [s.method, s]))
  const base = bt.baseline_12w
  const eng = bt.rules_engine
  const recent = bt.recent_4w

  const weeks = [...new Set(state.weekly.map(w => w.week))].sort()
  const totals = weeks.map(w => state.weekly.filter(x => x.week === w).reduce((s, x) => s + x.units, 0))
  const lastT = totals.at(-1) ?? 0
  const prevT = totals.at(-2) ?? 0
  const open = state.signals.filter(s => s.status === 'New' || s.status === 'Surfaced to procurement')
  const queue = [...reorders, ...pauses, ...decide]
  const maxW = Math.max(base?.WAPE ?? 0, eng?.WAPE ?? 0, recent?.WAPE ?? 0, 0.01)

  return (
    <Page
      title="Overview"
      crumb={`${dateLong(m.analysis_date)} · sales through ${m.anchor_week}`}
      action={
        <a className="btn btn-primary" href="#/workbench">
          Review decisions
        </a>
      }
    >
      <section className="welcome reveal-card" aria-label="This run">
        <div className="welcome-bg" aria-hidden="true">
          {!prefersReducedMotion() && (
            <DotGrid dotSize={3} gap={20} baseColor="#d5dbd8" activeColor="#15803d" proximity={130} strength={0.8} glow={0.35} fade={0.55} clickShock={false} intro />
          )}
        </div>
        <div className="welcome-inner">
          <div>
            <h2>
              {reorders.length} reorders and {pauses.length} pauses ready for sign-off
            </h2>
            <p>
              {m.planning_month_festival ? `${monthName(m.planning_month)} is a festival month, so demand carries Raghav's 25% uplift. ` : ''}
              Stock as of {m.analysis_date}; sales through {m.anchor_week}. Every line waits for a person.
            </p>
            <div className="welcome-tags">
              {m.planning_month_festival && <span className="tag warn">Festival month</span>}
              <span className="tag">{recs.length} SKUs</span>
              <span className="tag brand">{m.rule_version.replace('rules-', 'Rules ')}</span>
            </div>
          </div>
          <div className="toolbar-left">
            <a className="btn btn-secondary" href="#/planning">
              All SKUs
            </a>
            <a className="btn btn-primary" href="#/workbench">
              Open workbench <ArrowRight size={15} />
            </a>
          </div>
        </div>
      </section>

      <div className="kpis">
        <Kpi label="Reorders" dot="#dc2626" value={<Num to={reorders.length} />} note={`${fmt(units)} units recommended`} />
        <Kpi label="Orders paused" dot="#d97706" value={<Num to={pauses.length} />} note="Stock above the window" />
        <Kpi label="Awaiting a decision" value={<Num to={withRaghav + withProc} />} note={`${withRaghav} with Raghav · ${withProc} with procurement`} />
        <Kpi label="Exceptions" value={<Num to={review.length} />} note={review.length === 1 ? 'Needs Raghav’s judgment' : 'Need Raghav’s judgment'} tone={review.length ? 'warn' : undefined} />
        <Kpi label="Below minimum cover" value={<Num to={below.length} />} note={`${belowPerish} perishable`} tone={below.length ? 'up' : 'good'} />
        <Kpi
          label="Forecast error (WAPE)"
          value={
            <>
              <Num to={(base?.WAPE ?? 0) * 100} decimals={1} suffix="%" />
              <small>baseline</small>
            </>
          }
          note={`${pct(eng?.WAPE, 1, false)} with festival uplift`}
          tone="up"
        />
      </div>

      <div className="grid">
        <Card
          className="span-8"
          title="Weekly units sold"
          sub="All SKUs, 2026-W27 to W42. Shaded weeks fall in a festival month."
          right={
            <div style={{ textAlign: 'right' }}>
              <div className="kpi-value" style={{ fontSize: 20 }}>
                {fmt(lastT)}
              </div>
              <div className="kpi-note">{pct(prevT ? lastT / prevT - 1 : null)} vs last week</div>
            </div>
          }
        >
          <SalesChart weekly={state.weekly} />
        </Card>
        <Card className="span-4" title="Recommendation mix" sub="This run, by action">
          <div style={{ display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap' }}>
            <Donut
              label={String(recs.length)}
              sub="SKUs"
              data={[
                { label: 'Reorder', value: reorders.length, color: '#dc2626' },
                { label: 'Pause', value: pauses.length, color: '#d97706' },
                { label: 'No action', value: none.length, color: '#94a3b8' },
                { label: 'Planner decides', value: decide.length, color: '#334155' },
              ]}
            />
            <ul className="list" style={{ flex: 1, minWidth: 150 }}>
              {[
                ['Reorder', reorders.length, '#dc2626'],
                ['Pause', pauses.length, '#d97706'],
                ['No action', none.length, '#94a3b8'],
                ['Planner decides', decide.length, '#334155'],
              ].map(([l, v, c]) => (
                <li key={String(l)}>
                  <span className="state" style={{ ['--dot' as string]: String(c) }}>
                    {l}
                  </span>
                  <strong className="num">{v}</strong>
                </li>
              ))}
            </ul>
          </div>
        </Card>
      </div>

      <div className="grid">
        <Card className="span-8" title="Weeks of cover by SKU" sub="Stock ÷ festival-adjusted weekly demand. Select a SKU for its evidence.">
          <CoverChart />
        </Card>
        <div className="span-4" style={{ display: 'grid', gap: 16, alignContent: 'start' }}>
          <Card
            title="Forecast accuracy"
            sub={`One week ahead, ${fmt(base?.observations)} SKU-weeks`}
            foot={
              <>
                <span>The festival uplift overstates October demand.</span>
                <a className="textlink" href="#/backtest">
                  Details
                </a>
              </>
            }
          >
            {[
              ['12-week average', base, '#334155'],
              ['With festival uplift', eng, '#d97706'],
              ['4-week average', recent, '#0f766e'],
            ].map(([l, s, c]) => {
              const row = s as typeof base
              return (
                <div className="meter" key={String(l)} style={{ gridTemplateColumns: '1fr auto' }}>
                  <span className="small">{String(l)}</span>
                  <span className="meter-value" style={{ fontSize: 15 }}>
                    {pct(row?.WAPE, 1, false)}
                  </span>
                  <div className="meter-track" style={{ gridColumn: '1 / -1' }}>
                    <div className="meter-fill" style={{ width: `${((row?.WAPE ?? 0) / maxW) * 100}%`, background: String(c) }} />
                  </div>
                </div>
              )
            })}
          </Card>
          <Card
            title="Operations signals"
            sub={`Drops over ${Math.round(m.thresholds.signal_drop * 100)}% block ordering until acknowledged`}
            foot={
              <>
                <span>{state.signal_history.length} detected in earlier weeks</span>
                <a className="textlink" href="#/signals">
                  Signals
                </a>
              </>
            }
          >
            <div className="kpi-value">
              {open.length}
              <small>open in {m.anchor_week}</small>
            </div>
          </Card>
        </div>
      </div>

      <div className="grid">
        <Card
          className="span-12"
          title="Decision queue"
          sub="Reorders, pauses and planner decisions in this run"
          right={
            <a className="btn btn-secondary btn-small" href="#/workbench">
              Workbench
            </a>
          }
          bodyClass="flush"
        >
          <div className="table-scroll">
            <table className="data stack">
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Recommendation</th>
                  <th className="r">Quantity</th>
                  <th className="r">Weeks of cover</th>
                  <th>Why</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {queue.map(r => (
                  <tr key={r.sku_id} className="clickable" tabIndex={0} onClick={() => openSku(r.sku_id)} onKeyDown={e => e.key === 'Enter' && openSku(r.sku_id)}>
                    <td className="primary">
                      <strong>{r.sku_name.replace('Freshroots ', '')}</strong>
                      <span className="sub">
                        {r.sku_id} · {r.category}
                      </span>
                    </td>
                    <td data-label="Recommendation">
                      <span className={`state ${recState(r)}`}>{r.action}</span>
                    </td>
                    <td className="r" data-label="Quantity">
                      {r.recommended_qty === null ? 'Planner' : r.recommended_qty ? fmt(r.recommended_qty) : '—'}
                    </td>
                    <td className="r" data-label="Weeks of cover">
                      {r.cover_is_infinite ? '∞' : fmt(r.weeks_of_cover, 1)}
                    </td>
                    <td className="muted hide-sm">
                      {r.flags.filter(f => f !== 'FESTIVAL_UPLIFT_APPLIED').map(f => m.flag_labels[f] ?? f).join(' · ') || 'Within window'}
                    </td>
                    <td data-label="Status">
                      <span className={`state ${statusState(r.status)}`}>{r.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </Page>
  )
}
