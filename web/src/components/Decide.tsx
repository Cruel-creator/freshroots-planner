// Decision controls. The API enforces every rule; the UI mirrors them so blocked
// actions are visibly disabled with the reason, never silently missing.
import { useState } from 'react'
import { api, type Rec, type Signal } from '../api'
import { useApp } from '../ctx'
import { fmt } from '../format'

export function Decide({ rec, compact = false }: { rec: Rec; compact?: boolean }) {
  const { actor, act, state } = useApp()
  const [mode, setMode] = useState<'idle' | 'override' | 'reject'>('idle')
  const choices = state.meta.actions.filter(a => a !== state.meta.review_action)
  const [action, setAction] = useState(rec.action === state.meta.review_action ? choices[0] : rec.action)
  const [qty, setQty] = useState<string>(String(rec.recommended_qty ?? rec.max_qty_within_window ?? ''))
  const [reason, setReason] = useState('')
  const min = state.meta.min_reason
  const isReorder = state.meta.reorder_actions.includes(action)

  if (rec.status === 'Pending planner review') {
    if (actor.role !== 'planner')
      return <p className="hint">Waiting for Raghav (planner). Switch “Reading as” to decide.</p>
    const blocked = rec.action === state.meta.review_action
      ? 'The rules give no single answer here. Override with an action, quantity and reason.'
      : state.meta.reorder_actions.includes(rec.action) && !rec.recommended_qty
        ? 'Quantity is missing. Override with a quantity and reason.'
        : null
    return (
      <div className="stack-gap">
        <div className="toolbar-left">
          <button className="btn btn-primary" disabled={!!blocked} title={blocked ?? undefined} onClick={() => act(`Approved ${rec.sku_id}`, () => api.approve(rec.rec_id, actor.name))}>
            Approve{rec.recommended_qty ? ` ${fmt(rec.recommended_qty)} units` : ''}
          </button>
          <button className="btn btn-quiet" aria-pressed={mode === 'override'} onClick={() => setMode(mode === 'override' ? 'idle' : 'override')}>
            Override
          </button>
          <button className="btn btn-danger" aria-pressed={mode === 'reject'} onClick={() => setMode(mode === 'reject' ? 'idle' : 'reject')}>
            Reject
          </button>
        </div>
        {blocked && <p className="hint">{blocked}</p>}
        {mode !== 'idle' && (
          <form
            className="form-grid"
            onSubmit={async e => {
              e.preventDefault()
              const ok =
                mode === 'override'
                  ? await act(`Override saved for ${rec.sku_id}`, () => api.override(rec.rec_id, actor.name, action, isReorder ? Number(qty) : 0, reason))
                  : await act(`Rejected ${rec.sku_id}`, () => api.reject(rec.rec_id, actor.name, reason))
              if (ok) {
                setMode('idle')
                setReason('')
              }
            }}
          >
            {mode === 'override' && (
              <>
                <div className="field">
                  <label htmlFor={`act-${rec.rec_id}`}>Action</label>
                  <select id={`act-${rec.rec_id}`} className="select" value={action} onChange={e => setAction(e.target.value)}>
                    {choices.map(c => (
                      <option key={c}>{c}</option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label htmlFor={`qty-${rec.rec_id}`}>Quantity (units)</label>
                  <input id={`qty-${rec.rec_id}`} className="input" type="number" min={0} step={10} value={isReorder ? qty : '0'} disabled={!isReorder} onChange={e => setQty(e.target.value)} />
                </div>
              </>
            )}
            <div className="field full">
              <label htmlFor={`why-${rec.rec_id}`}>Reason</label>
              <textarea id={`why-${rec.rec_id}`} className="textarea" placeholder="Why the rule output is being changed" value={reason} onChange={e => setReason(e.target.value)} />
              <span className="hint">
                {reason.trim().length}/{min} characters minimum. Saved to the audit log with your name.
              </span>
            </div>
            <div className="full toolbar-left">
              <button className={`btn ${mode === 'reject' ? 'btn-danger' : 'btn-primary'}`} type="submit" disabled={reason.trim().length < min || (mode === 'override' && isReorder && !(Number(qty) > 0))}>
                {mode === 'override' ? 'Save override' : 'Reject recommendation'}
              </button>
              <button type="button" className="btn btn-quiet" onClick={() => setMode('idle')}>
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>
    )
  }

  if (rec.status === 'Pending procurement approval') {
    const open = state.signals.filter(s => s.sku_id === rec.sku_id && (s.status === 'New' || s.status === 'Surfaced to procurement'))
    if (actor.role !== 'procurement')
      return (
        <p className="hint">
          Waiting for procurement to approve {fmt(rec.final_qty)} units.{open.length ? ' A sales alert is still open for this product.' : ''}
        </p>
      )
    return (
      <div className="stack-gap">
        {open.length > 0 && <p className="hint warn">Held: {open.length} open sales alert{open.length === 1 ? '' : 's'}. Priya must triage and you must acknowledge {open.length === 1 ? 'it' : 'them'} on Sales alerts.</p>}
        <div className="toolbar-left">
          <button className="btn btn-primary" disabled={open.length > 0} onClick={() => act(`Approved PO line ${rec.sku_id}`, () => api.procure(rec.rec_id, actor.name))}>
            Approve PO line · {fmt(rec.final_qty)} units
          </button>
          {!compact && (
            <button className="btn btn-danger" aria-pressed={mode === 'reject'} onClick={() => setMode(mode === 'reject' ? 'idle' : 'reject')}>
              Reject
            </button>
          )}
        </div>
        {mode === 'reject' && (
          <form
            className="stack-gap"
            onSubmit={async e => {
              e.preventDefault()
              if (await act(`Rejected ${rec.sku_id}`, () => api.reject(rec.rec_id, actor.name, reason))) setMode('idle')
            }}
          >
            <textarea className="textarea" aria-label="Reason" placeholder="Why procurement is rejecting this line" value={reason} onChange={e => setReason(e.target.value)} />
            <button className="btn btn-danger" disabled={reason.trim().length < min}>
              Reject line
            </button>
          </form>
        )}
      </div>
    )
  }

  return (
    <p className="hint">
      {rec.status}
      {rec.planner_reason ? ` · “${rec.planner_reason}”` : ''}
    </p>
  )
}

export function Triage({ signal }: { signal: Signal }) {
  const { actor, act, state } = useApp()
  const [note, setNote] = useState('')
  const [decision, setDecision] = useState(state.meta.signal_decisions[0])
  const sid = signal.sid!
  if (signal.status === 'New') {
    if (actor.role !== 'analyst') return <p className="hint">Waiting for Priya (analyst) to triage.</p>
    return (
      <div className="stack-gap">
        <textarea className="textarea" aria-label="Note" placeholder="Note (required to dismiss)" value={note} onChange={e => setNote(e.target.value)} />
        <div className="toolbar-left">
          <button className="btn btn-primary" onClick={() => act('Signal surfaced to procurement', () => api.surface(sid, actor.name, note))}>
            Surface to procurement
          </button>
          <button className="btn btn-quiet" disabled={note.trim().length < state.meta.min_reason} onClick={() => act('Signal dismissed', () => api.dismiss(sid, actor.name, note))}>
            Dismiss
          </button>
        </div>
      </div>
    )
  }
  if (signal.status === 'Surfaced to procurement') {
    if (actor.role !== 'procurement') return <p className="hint">Waiting for procurement to acknowledge.</p>
    return (
      <div className="stack-gap">
        <div className="seg" role="group" aria-label="Decision">
          {state.meta.signal_decisions.map(d => (
            <button key={d} aria-pressed={decision === d} onClick={() => setDecision(d)}>
              {d}
            </button>
          ))}
        </div>
        <textarea className="textarea" aria-label="Note" placeholder="What you checked (required)" value={note} onChange={e => setNote(e.target.value)} />
        <button className="btn btn-primary" disabled={note.trim().length < state.meta.min_reason} onClick={() => act('Signal acknowledged', () => api.acknowledge(sid, actor.name, decision, note))}>
          Acknowledge
        </button>
      </div>
    )
  }
  return (
    <p className="hint">
      {signal.status}
      {signal.decision ? ` · ${signal.decision}` : ''}
      {signal.note ? ` · “${signal.note}”` : ''}
    </p>
  )
}
