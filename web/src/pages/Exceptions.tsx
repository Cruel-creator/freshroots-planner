import { useEffect, useState } from 'react'
import { ChevronRight } from 'lucide-react'
import { api } from '../api'
import { useApp } from '../ctx'
import { Card, Kpi, Page } from '../components/Nav'
import { Decide } from '../components/Decide'
import { cover, fmt, numberWord, statusState } from '../format'

type AiNote = { note: string; category: string }

export function Exceptions() {
  const { state, openSku } = useApp()
  const aiOn = state.meta.llm_provider !== 'disabled'
  const [notes, setNotes] = useState<Record<string, AiNote> | null>(null)
  const [aiError, setAiError] = useState('')

  useEffect(() => {
    if (!aiOn) return
    let live = true
    api
      .aiNotes()
      .then(r => {
        if (!live) return
        setNotes(Object.fromEntries(r.notes.map(n => [`${n.sku_id}|${n.code}`, n])))
        setAiError(r.error ?? '')
      })
      .catch(e => {
        if (!live) return
        setNotes({})
        setAiError(String(e))
      })
    return () => {
      live = false
    }
  }, [aiOn])
  const review = state.recommendations.filter(r => r.needs_review || r.action === state.meta.review_action)
  const pending = review.filter(r => r.status === 'Pending planner review').length
  const conflicts = state.exceptions.filter(e => e.code === 'RULE_CONFLICT').length
  const label = (flags: string) =>
    flags
      .split(',')
      .map(f => f.trim())
      .filter(f => f && f !== 'none')
      .map(f => state.meta.flag_labels[f] ?? f.replaceAll('_', ' ').toLowerCase())
      .join(' · ') || 'No rule flags'

  return (
    <Page
      kicker="Exceptions"
      title={review.length ? `${review.length === 1 ? 'One case' : `${numberWord(review.length)} cases`} the rules can't settle alone.` : 'The rules settle every line this week.'}
      crumb="Each one goes to Raghav with its evidence. A person decides; the rules never set the quantity on their own."
    >
      <div className="kpis" style={{ ['--n' as string]: 3 }}>
        <Kpi label="Products needing Raghav" value={review.length} />
        <Kpi label="Still pending" value={pending} tone={pending ? 'warn' : 'good'} note={pending ? 'Awaiting a decision' : 'All decided'} />
        <Kpi label="Rule conflicts" value={conflicts} note={`${state.exceptions.length} exception${state.exceptions.length === 1 ? '' : 's'} in total`} />
      </div>

      {!review.length && (
        <Card title="Nothing needs Raghav">
          <p className="empty">No exceptions in this run.</p>
        </Card>
      )}
      <div style={{ display: 'grid', gap: 40 }}>
        {review.map(r => {
          const ex = state.exceptions.filter(e => e.sku_id === r.sku_id)
          return (
            <Card
              key={r.sku_id}
              title={r.sku_name.replace('Freshroots ', '')}
              sub={`${r.sku_id} · ${r.category} · assigned to Raghav Kulkarni`}
              right={<span className={`state ${statusState(r.status)}`}>{r.status}</span>}
              foot={
                <>
                  <span>
                    {cover(r)} weeks of cover · {r.recommended_qty === null ? 'no quantity' : `${fmt(r.recommended_qty)} units`} · {r.action.toLowerCase()}
                  </span>
                  <button className="textlink" onClick={() => openSku(r.sku_id)}>
                    Open the evidence <ChevronRight size={15} />
                  </button>
                </>
              }
            >
              {ex.map(e => (
                <div key={e.code} className="grid" style={{ marginBottom: 18, rowGap: 14 }}>
                  <dl className="kv span-6">
                    <dt>Signal</dt>
                    <dd>{e.signal}</dd>
                    <dt>Rules</dt>
                    <dd>{label(e.rules_triggered)}</dd>
                  </dl>
                  <dl className="kv span-6">
                    <dt>Why a person</dt>
                    <dd>{e.why_not_automated}</dd>
                    <dt>Next</dt>
                    <dd>{e.suggested_action}</dd>
                    {aiOn && (
                      <>
                        <dt>AI note</dt>
                        <dd>
                          {notes === null
                            ? 'Asking Gemini…'
                            : notes[`${e.sku_id}|${e.code}`]
                              ? `${notes[`${e.sku_id}|${e.code}`].category}: ${notes[`${e.sku_id}|${e.code}`].note}`
                              : aiError || 'No note for this exception.'}
                        </dd>
                      </>
                    )}
                  </dl>
                </div>
              ))}
              {!ex.length && r.review_reasons.length > 0 && <p className="small muted">{r.review_reasons.join('; ')}</p>}
              <p className="small muted">{r.explanation}</p>
              <Decide rec={r} />
            </Card>
          )
        })}
      </div>
      <p className="fine" style={{ marginTop: 24 }}>
        Exceptions come from deterministic checks (modified z-score, 20% demand drop) and rule conflicts. They never change a calculation.{' '}
        {aiOn
          ? 'AI notes are written by Gemini from the facts shown here only. They suggest what to check; they never set a quantity, an action or a status.'
          : 'AI notes are off: no Gemini API key is configured.'}
      </p>
    </Page>
  )
}
