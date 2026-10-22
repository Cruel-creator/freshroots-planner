// The Planning Brief shell: a masthead, a sticky section bar, and editorial building blocks
// (page head, ruled sections, figure strips) that every page is set in.
import type { ReactNode } from 'react'
import { useApp } from '../ctx'
import { dateLong } from '../format'

export const ROUTES = [
  { path: '', label: 'The brief' },
  { path: 'planning', label: 'Products' },
  { path: 'exceptions', label: 'Exceptions' },
  { path: 'workbench', label: 'Approvals' },
  { path: 'signals', label: 'Sales alerts' },
  { path: 'backtest', label: 'Forecast' },
  { path: 'data', label: 'Data' },
  { path: 'plan', label: 'Plan' },
]

function Reader({ className }: { className: string }) {
  const { state, actor, setActor } = useApp()
  return (
    <label className={`reader ${className}`}>
      Reading as
      <select value={actor.name} onChange={e => setActor(e.target.value)} aria-label="Reading as">
        {state.meta.actors.map(a => (
          <option key={a.name} value={a.name}>
            {a.name}, {a.role}
          </option>
        ))}
      </select>
    </label>
  )
}

export function Shell({ route, children }: { route: string; children: ReactNode }) {
  const { state } = useApp()
  const m = state.meta
  const recs = state.recommendations
  const counts: Record<string, number> = {
    planning: recs.length,
    exceptions: recs.filter(r => (r.needs_review || r.action === m.review_action) && r.status === 'Pending planner review').length,
    workbench: recs.filter(r => r.status === 'Pending planner review' || r.status === 'Pending procurement approval').length,
    signals: state.signals.filter(s => s.status === 'New' || s.status === 'Surfaced to procurement').length,
  }
  const issue = Number(m.anchor_week.split('-W')[1]) || ''
  return (
    <>
      <header className="mast wrap">
        <div className="mast-row">
          <a className="wordmark" href="#/">
            Freshroots <i>Planning Brief</i>
          </a>
          <span className="issue num">
            No. {issue} · {dateLong(m.analysis_date)}
          </span>
        </div>
        <Reader className="reader-m" />
        <div className="mast-rule" />
      </header>
      <div className="sections-bar">
        <div className="sections wrap">
          <nav aria-label="Sections">
            {ROUTES.map(r => (
              <a key={r.path} href={`#/${r.path}`} aria-current={route === r.path ? 'page' : undefined}>
                {r.label}
                {counts[r.path] ? <em className="num">{counts[r.path]}</em> : null}
              </a>
            ))}
          </nav>
          <Reader className="reader-d" />
        </div>
      </div>
      <div className="wrap">{children}</div>
    </>
  )
}

/** Inner pages: a kicker, a headline that states the finding, a lede, and at most one or two actions. */
export function Page({ kicker, title, crumb, action, head = true, children }: { kicker?: string; title: ReactNode; crumb?: ReactNode; action?: ReactNode; head?: boolean; children: ReactNode }) {
  return (
    <main className="content">
      {head && (
        <header className="phead">
          <div>
            {kicker && <div className="sc">{kicker}</div>}
            <h1>{title}</h1>
            {crumb && <p className="lede">{crumb}</p>}
          </div>
          {action && <div className="phead-act">{action}</div>}
        </header>
      )}
      {children}
      <Colophon />
    </main>
  )
}

export function Colophon() {
  const { state } = useApp()
  return (
    <footer className="colophon">
      <i>Suggestions come from Raghav's documented rules; decisions are his and procurement's.</i>
      <span className="num">
        {state.meta.rule_version.replace('rules-', 'Rules ')} · run {state.meta.run.run_id.replace('RUN-', '')} · draft only, nothing leaves this app
      </span>
    </footer>
  )
}

/** A ruled section: serif title over a hairline, no box. */
export function Card({ title, sub, right, foot, className = '', bodyClass = '', children }: { title?: ReactNode; sub?: ReactNode; right?: ReactNode; foot?: ReactNode; className?: string; bodyClass?: string; children: ReactNode }) {
  return (
    <section className={`card ${className}`}>
      {(title || right) && (
        <div className="card-head">
          <div>
            {title && <h3 className="card-title">{title}</h3>}
            {sub && <p className="card-sub">{sub}</p>}
          </div>
          {right}
        </div>
      )}
      <div className={`card-body ${bodyClass}`}>{children}</div>
      {foot && <div className="card-foot">{foot}</div>}
    </section>
  )
}

/** One figure in a ruled strip: the number first, then what it counts. */
export function Kpi({ label, value, note, tone, dot }: { label: string; value: ReactNode; note?: ReactNode; tone?: 'up' | 'good' | 'warn'; dot?: string }) {
  return (
    <div className="kpi">
      <span className="kpi-label">
        {dot && <span className="kpi-dot" style={{ ['--dot' as string]: dot }} />}
        {label}
      </span>
      <span className="kpi-value">{value}</span>
      {note && <span className={`kpi-note ${tone ?? ''}`}>{note}</span>}
    </div>
  )
}
