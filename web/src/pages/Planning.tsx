import { useMemo, useState } from 'react'
import { ArrowDown, ArrowUp, Download } from 'lucide-react'
import { useApp } from '../ctx'
import { Card, Page } from '../components/Nav'
import { fmt, pct, recState, statusState } from '../format'
import type { Rec } from '../api'

type Key = 'sku_id' | 'recent_4w_avg' | 'baseline_12w_avg' | 'demand_change_pct' | 'adjusted_weekly_demand' | 'current_stock' | 'weeks_of_cover' | 'recommended_qty'
const FILTERS = ['All', 'Needs decision', 'Reorder', 'Pause', 'Perishable'] as const

export function Planning() {
  const { state, openSku, runId } = useApp()
  const [q, setQ] = useState('')
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>('All')
  const [cat, setCat] = useState('')
  const [dist, setDist] = useState('')
  const [sort, setSort] = useState<{ key: Key; dir: 1 | -1 }>({ key: 'weeks_of_cover', dir: 1 })
  const cats = [...new Set(state.recommendations.map(r => r.category))].sort()
  const dists = [...new Set(state.recommendations.map(r => r.mapped_distributor))].sort()

  const rows = useMemo(() => {
    const v = (r: Rec, k: Key) => (k === 'weeks_of_cover' && r.cover_is_infinite ? 1e9 : (r[k] as number | string | null) ?? -1e9)
    return state.recommendations
      .filter(r => !q || `${r.sku_id} ${r.sku_name}`.toLowerCase().includes(q.toLowerCase()))
      .filter(r => !cat || r.category === cat)
      .filter(r => !dist || r.mapped_distributor === dist)
      .filter(r =>
        filter === 'All' ? true
          : filter === 'Needs decision' ? r.needs_review || r.action === state.meta.review_action
          : filter === 'Reorder' ? state.meta.reorder_actions.includes(r.action)
          : filter === 'Pause' ? r.action === 'Pause next order'
          : !!r.is_perishable,
      )
      .sort((a, b) => {
        const x = v(a, sort.key)
        const y = v(b, sort.key)
        return (x < y ? -1 : x > y ? 1 : 0) * sort.dir
      })
  }, [state, q, cat, dist, filter, sort])

  const H = ({ k, children, right = false }: { k: Key; children: string; right?: boolean }) => (
    <th className={right ? 'r' : undefined} aria-sort={sort.key === k ? (sort.dir === 1 ? 'ascending' : 'descending') : 'none'}>
      <button onClick={() => setSort(s => ({ key: k, dir: s.key === k ? ((-s.dir) as 1 | -1) : 1 }))}>
        {children}
        {sort.key === k ? sort.dir === 1 ? <ArrowUp size={12} /> : <ArrowDown size={12} /> : null}
      </button>
    </th>
  )

  return (
    <Page
      kicker="Products"
      title="Every product, and what the rules suggest."
      crumb="Sales are per product across all distributors. Select a row for its chart, formulas, source rows and the decision."
      action={
        <a className="btn btn-secondary" href={`/api/runs/${encodeURIComponent(runId)}/recommendations.csv`}>
          <Download size={15} /> Export CSV
        </a>
      }
    >
      <Card title={`${rows.length} of ${state.recommendations.length} products`} sub="Sorted by weeks of stock left, least first. Select a column heading to sort by it." bodyClass="flush">
        <div className="toolbar">
          <div className="toolbar-left">
            <input className="search" type="search" placeholder="Search products" aria-label="Search products" value={q} onChange={e => setQ(e.target.value)} />
            <div className="seg" role="group" aria-label="Filter">
              {FILTERS.map(f => (
                <button key={f} aria-pressed={filter === f} onClick={() => setFilter(f)}>
                  {f}
                </button>
              ))}
            </div>
          </div>
          <div className="toolbar-right">
            <select className="select" style={{ width: 'auto' }} aria-label="Category" value={cat} onChange={e => setCat(e.target.value)}>
              <option value="">All categories</option>
              {cats.map(c => (
                <option key={c}>{c}</option>
              ))}
            </select>
            <select className="select" style={{ width: 'auto' }} aria-label="Mapped distributor" value={dist} onChange={e => setDist(e.target.value)}>
              <option value="">All distributors</option>
              {dists.map(c => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="table-scroll tall">
          <table className="data stack">
            <thead>
              <tr>
                <H k="sku_id">Product</H>
                <H k="recent_4w_avg" right>
                  4-wk avg
                </H>
                <H k="baseline_12w_avg" right>
                  12-wk avg
                </H>
                <H k="demand_change_pct" right>
                  Change
                </H>
                <H k="adjusted_weekly_demand" right>
                  Expected / wk
                </H>
                <H k="current_stock" right>
                  Stock
                </H>
                <H k="weeks_of_cover" right>
                  Weeks left
                </H>
                <th>Suggested</th>
                <H k="recommended_qty" right>
                  Units
                </H>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(r => (
                <tr key={r.sku_id} className="clickable" tabIndex={0} onClick={() => openSku(r.sku_id)} onKeyDown={e => e.key === 'Enter' && openSku(r.sku_id)}>
                  <td className="primary">
                    <strong>{r.sku_name.replace('Freshroots ', '')}</strong>
                    <span className="sub">
                      {r.sku_id} · {r.category}
                      {r.is_perishable ? ' · perishable' : ''}
                    </span>
                  </td>
                  <td className="r hide-sm">{fmt(r.recent_4w_avg, 1)}</td>
                  <td className="r hide-sm">{fmt(r.baseline_12w_avg, 1)}</td>
                  <td className={`r hide-sm ${(r.demand_change_pct ?? 0) > state.meta.thresholds.high_demand ? 'hl-orange' : ''}`}>
                    {pct(r.demand_change_pct)}
                  </td>
                  <td className="r hide-sm">{fmt(r.adjusted_weekly_demand, 1)}</td>
                  <td className="r hide-sm">{fmt(r.current_stock)}</td>
                  <td className="r" data-label="Weeks left">
                    <strong>{r.cover_is_infinite ? '∞' : fmt(r.weeks_of_cover, 1)}</strong>
                  </td>
                  <td data-label="Suggested">
                    <span className={`state ${recState(r)}`}>{r.action}</span>
                  </td>
                  <td className="r" data-label="Units">
                    {r.recommended_qty === null ? '—' : r.recommended_qty ? fmt(r.recommended_qty) : '—'}
                  </td>
                  <td data-label="Status">
                    <span className={`state ${statusState(r.status)}`}>{r.status}</span>
                  </td>
                </tr>
              ))}
              {!rows.length && (
                <tr>
                  <td colSpan={10} className="empty">
                    No products match these filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      <div className="grid">
        <Card className="span-12" title="How the rules decide" sub="When more than one rule fires, this order picks the action. Every flag is still shown. A prototype assumption until Raghav confirms it.">
          {state.readiness.priority_steps.map(p => (
            <details className="disclose" key={p.step}>
              <summary>{p.step}</summary>
              <div className="small muted">{p.rule}</div>
            </details>
          ))}
        </Card>
      </div>
    </Page>
  )
}
