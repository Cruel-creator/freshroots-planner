// Dashboard shell: sidebar navigation, sticky page header, page content.
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { Activity, AlertTriangle, CalendarRange, ClipboardCheck, Database, LayoutDashboard, LineChart, Menu, Sprout, Table2 } from 'lucide-react'
import { useApp } from '../ctx'
import { lockScroll } from '../motion'

export const ROUTES = [
  { path: '', label: 'Overview', icon: LayoutDashboard },
  { path: 'planning', label: 'Planning', icon: Table2 },
  { path: 'exceptions', label: 'Exceptions', icon: AlertTriangle },
  { path: 'workbench', label: 'Workbench', icon: ClipboardCheck },
  { path: 'signals', label: 'Signals', icon: Activity },
  { path: 'backtest', label: 'Backtest', icon: LineChart },
  { path: 'data', label: 'Data', icon: Database },
  { path: 'plan', label: 'Plan', icon: CalendarRange },
]

const MenuCtx = createContext<{ open: boolean; setOpen: (v: boolean) => void }>({ open: false, setOpen: () => undefined })

export function Shell({ route, children }: { route: string; children: ReactNode }) {
  const [open, setOpen] = useState(false)
  useEffect(() => setOpen(false), [route])
  useEffect(() => {
    lockScroll(open)
    return () => lockScroll(false)
  }, [open])
  return (
    <MenuCtx.Provider value={{ open, setOpen }}>
      <div className="app">
        <Sidebar route={route} open={open} />
        {open && <div className="scrim open" style={{ zIndex: 29 }} onClick={() => setOpen(false)} aria-hidden="true" />}
        <div className="main">{children}</div>
      </div>
    </MenuCtx.Provider>
  )
}

function Sidebar({ route, open }: { route: string; open: boolean }) {
  const { state } = useApp()
  const counts: Record<string, number> = {
    exceptions: state.recommendations.filter(r => (r.needs_review || r.action === state.meta.review_action) && r.status === 'Pending planner review').length,
    workbench: state.recommendations.filter(r => r.status === 'Pending planner review' || r.status === 'Pending procurement approval').length,
    signals: state.signals.filter(s => s.status === 'New' || s.status === 'Surfaced to procurement').length,
  }
  return (
    <aside className={`sidebar ${open ? 'open' : ''}`} aria-label="Main navigation">
      <a className="brand" href="#/">
        <span className="brand-mark">
          <Sprout size={16} />
        </span>
        <span>
          Freshroots
          <small>Demand planning</small>
        </span>
      </a>
      <nav>
        {ROUTES.map(r => {
          const Icon = r.icon
          return (
            <a key={r.path} className="nav-item" href={`#/${r.path}`} aria-current={route === r.path ? 'page' : undefined}>
              <Icon size={17} strokeWidth={1.8} />
              {r.label}
              {counts[r.path] ? <span className="nav-count">{counts[r.path]}</span> : null}
            </a>
          )
        })}
      </nav>
      <div className="sidebar-foot">
        <b>Run</b> {state.meta.run.run_id.slice(4, 19)}
        <br />
        <b>Stock as of</b> {state.meta.analysis_date}
        <br />
        <b>Rules</b> {state.meta.rule_version.replace('rules-', '')}
        <br />
        <span>No purchase order leaves this app.</span>
      </div>
    </aside>
  )
}

export function Page({ title, crumb, action, children }: { title: string; crumb?: string; action?: ReactNode; children: ReactNode }) {
  const { state, actor, setActor } = useApp()
  const { setOpen } = useContext(MenuCtx)
  return (
    <>
      <header className="header">
        <button className="icon-btn menu-btn" aria-label="Open navigation" onClick={() => setOpen(true)}>
          <Menu size={18} />
        </button>
        <h1>{title}</h1>
        {crumb && <span className="crumb">{crumb}</span>}
        <div className="header-right">
          <label className="actor">
            <span>Acting as</span>
            <select value={actor.name} onChange={e => setActor(e.target.value)} aria-label="Acting as">
              {state.meta.actors.map(a => (
                <option key={a.name} value={a.name}>
                  {a.name} · {a.role}
                </option>
              ))}
            </select>
          </label>
          {action}
        </div>
      </header>
      <main className="content page-enter">{children}</main>
    </>
  )
}

/** Card with a head (title, optional subtitle and right-side slot) and body. */
export function Card({ title, sub, right, foot, className = '', bodyClass = '', children }: { title?: string; sub?: ReactNode; right?: ReactNode; foot?: ReactNode; className?: string; bodyClass?: string; children: ReactNode }) {
  return (
    <section className={`card reveal-card ${className}`}>
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

export function Kpi({ label, value, note, tone, dot }: { label: string; value: ReactNode; note?: ReactNode; tone?: 'up' | 'good' | 'warn'; dot?: string }) {
  return (
    <div className="card kpi reveal-card">
      <span className="kpi-label">
        {dot && <span className="kpi-dot" style={{ ['--dot' as string]: dot }} />}
        {label}
      </span>
      <span className="kpi-value">{value}</span>
      {note && <span className={`kpi-note ${tone ?? ''}`}>{note}</span>}
    </div>
  )
}
