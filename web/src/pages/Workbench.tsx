import { useEffect, useState } from 'react'
import { Download } from 'lucide-react'
import { api, downloadText } from '../api'
import { useApp } from '../ctx'
import { Card, Kpi, Page } from '../components/Nav'
import { PALETTE } from '../components/Charts'
import { fmt, statusState } from '../format'

export function Workbench() {
  const { state, actor, act, runId, setRunId, openSku, toast } = useApp()
  const recs = state.recommendations
  const count = (s: string) => recs.filter(r => r.status === s).length
  const clean = recs.filter(r => r.status === 'Pending planner review' && !r.needs_review && r.action !== state.meta.review_action)
  const ready = count('Procurement approved')
  const [po, setPo] = useState<{ id: string; csv: string; rows: Record<string, string | number>[] } | null>(null)
  const [events, setEvents] = useState<Record<string, string | null>[]>([])

  useEffect(() => {
    let live = true
    api.events(runId).then(e => live && setEvents(e)).catch(() => undefined)
    return () => {
      live = false
    }
  }, [runId, state])

  const createPo = async () => {
    try {
      const res = await api.draftPo(runId, actor.name)
      setPo(res)
      toast(`${res.id} created. Not submitted.`)
      await act('Lines marked exported as draft', async () => undefined)
    } catch (e) {
      toast(e instanceof Error ? e.message : String(e), 'error')
    }
  }

  const primary =
    actor.role === 'planner' ? (
      <button className="btn btn-primary" disabled={!clean.length} onClick={() => act(`Approved ${clean.length} clean lines`, () => api.bulkApprove(runId, actor.name))}>
        Approve {clean.length} clean
      </button>
    ) : actor.role === 'procurement' ? (
      <button className="btn btn-primary" disabled={!ready} onClick={createPo}>
        Create draft PO
      </button>
    ) : null

  return (
    <Page
      kicker="Approvals"
      title="Raghav signs first. Procurement signs second."
      crumb="Every line needs Raghav's sign-off, and every order line needs procurement's. The draft PO is a file; nothing is submitted from here."
      action={primary}
    >
      <div className="kpis" style={{ ['--n' as string]: 5 }}>
        <Kpi label="With Raghav" value={count('Pending planner review')} dot={PALETTE.ochreDot} />
        <Kpi label="Signed off, no order" value={count('Planner approved') + count('Planner overridden')} />
        <Kpi label="With procurement" value={count('Pending procurement approval')} dot={PALETTE.ochreDot} />
        <Kpi label="Approved to order" value={ready} dot={PALETTE.moss} />
        <Kpi label="Exported as draft" value={count('Exported as draft')} />
      </div>

      <Card
        title="Lines in this run"
        sub={state.meta.inputs_changed ? 'Source files changed since this run. Start a new run to use the current data.' : `${recs.length} products in this run`}
        right={
          <div className="toolbar-right">
            <select className="select" style={{ width: 'auto', maxWidth: 300 }} value={runId} onChange={e => setRunId(e.target.value)} aria-label="Recommendation run">
              {state.meta.runs.map(r => (
                <option key={r.run_id} value={r.run_id}>
                  {r.run_id} · {r.created_by}
                </option>
              ))}
            </select>
            <button
              className="btn btn-secondary btn-small"
              onClick={async () => {
                try {
                  const r = await api.newRun(actor.name)
                  setRunId(r.run_id)
                  toast(`Started ${r.run_id}`)
                } catch (e) {
                  toast(e instanceof Error ? e.message : String(e), 'error')
                }
              }}
            >
              New run
            </button>
            <a className="btn btn-secondary btn-small" href={api.csv.recommendations(runId)}>
              <Download size={14} /> CSV
            </a>
          </div>
        }
        bodyClass="flush"
      >
        <div className="table-scroll tall">
          <table className="data stack">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Rule output</th>
                <th className="r">Rec. qty</th>
                <th>Final</th>
                <th className="r">Final qty</th>
                <th>Human checkpoints</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {recs.map(r => (
                <tr key={r.sku_id}>
                  <td className="primary">
                    <strong>{r.sku_name.replace('Freshroots ', '')}</strong>
                    <span className="sub">{r.sku_id}</span>
                  </td>
                  <td data-label="Rule output">
                    {r.action}
                    {r.conflicts.length ? <span className="sub" style={{ color: 'var(--warn-ink)' }}>Conflict</span> : null}
                  </td>
                  <td className="r" data-label="Rec. qty">
                    {r.recommended_qty === null ? '—' : fmt(r.recommended_qty)}
                  </td>
                  <td className="hide-sm">{r.final_action ?? '—'}</td>
                  <td className="r" data-label="Final qty">
                    {r.final_qty === null ? '—' : fmt(r.final_qty)}
                  </td>
                  <td className="small muted hide-sm">{r.checkpoints.join(' · ')}</td>
                  <td data-label="Status">
                    <span className={`state ${statusState(r.status)}`}>{r.status}</span>
                  </td>
                  <td className="r action">
                    <button className="btn btn-small btn-secondary" onClick={() => openSku(r.sku_id)}>
                      {r.status.startsWith('Pending') ? 'Decide' : 'View'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {po && (
        <div className="grid">
          <Card
            className="span-12"
            title={po.id}
            sub="Draft, not submitted. Supplier, price and delivery are not in the source data, so procurement fills them in Zoho."
            right={
              <button className="btn btn-primary btn-small" onClick={() => downloadText(`${po.id}.csv`, po.csv)}>
                <Download size={14} /> Download
              </button>
            }
            bodyClass="flush"
          >
            <div className="table-scroll">
              <table className="data stack">
                <thead>
                  <tr>
                    <th>Line</th>
                    <th>SKU</th>
                    <th className="r">Quantity</th>
                    <th>Planner decision</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {po.rows.map(row => (
                    <tr key={String(row.Line)}>
                      <td data-label="Line">{row.Line}</td>
                      <td className="primary">
                        {row.SKU_Name}
                        <span className="sub">{row.SKU_ID}</span>
                      </td>
                      <td className="r" data-label="Quantity">
                        {fmt(Number(row.Quantity))}
                      </td>
                      <td data-label="Planner">{row.Planner_Decision}</td>
                      <td data-label="Status">{row.Status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      <div className="grid">
        <Card
          className="span-12"
          title={`Audit log · ${events.length} events`}
          sub="Every generation, routing, approval, override, rejection and export, with who and when (UTC)."
          right={
            <a className="btn btn-secondary btn-small" href={api.csv.audit(runId)}>
              <Download size={14} /> CSV
            </a>
          }
          bodyClass="flush"
        >
          <details className="disclose">
            <summary>Show events</summary>
            <div className="table-scroll">
              <table className="data stack">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Who</th>
                    <th>Event</th>
                    <th>Item</th>
                    <th>To</th>
                    <th>Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {[...events].reverse().map(e => (
                    <tr key={String(e.event_id)}>
                      <td className="small" data-label="Time">
                        {e.ts?.replace('T', ' ').slice(0, 19)}
                      </td>
                      <td className="small" data-label="Who">
                        {e.actor}
                        <span className="sub">{e.role}</span>
                      </td>
                      <td className="small" data-label="Event">
                        {e.event_type?.replaceAll('_', ' ')}
                      </td>
                      <td className="small" data-label="Item">
                        {e.rec_id?.split(/[:|]/).slice(1).join(' ') || '—'}
                      </td>
                      <td className="small" data-label="To">
                        {e.to_status ?? '—'}
                      </td>
                      <td className="small muted" data-label="Reason">
                        {e.reason ?? ''}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </Card>
      </div>
    </Page>
  )
}
