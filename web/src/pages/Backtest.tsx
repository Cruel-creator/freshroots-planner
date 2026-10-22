import { useEffect, useState } from 'react'
import { api, type BacktestPayload } from '../api'
import { useApp } from '../ctx'
import { Card, Kpi, Page } from '../components/Nav'
import { PALETTE, WeekColumns } from '../components/Charts'
import { fmt } from '../format'

const ORDER = ['baseline_12w', 'rules_engine', 'recent_4w']
const LABEL: Record<string, string> = { baseline_12w: '12-week average', rules_engine: 'With festival uplift', recent_4w: '4-week average' }
const COLOR: Record<string, string> = { baseline_12w: PALETTE.ink2, rules_engine: PALETTE.brick, recent_4w: PALETTE.faint }

export function Backtest() {
  const { state, toast } = useApp()
  const [h, setH] = useState(1)
  const [bt, setBt] = useState<BacktestPayload>(state.backtest)

  useEffect(() => {
    if (h === 1) {
      setBt(state.backtest)
      return
    }
    let live = true
    api.backtest(h).then(b => live && setBt(b)).catch(e => toast(String(e), 'error'))
    return () => {
      live = false
    }
  }, [h, state.backtest, toast])

  const by = Object.fromEntries(bt.summary.map(s => [s.method, s]))
  const beats = by.rules_engine && by.baseline_12w ? by.rules_engine.WAPE < by.baseline_12w.WAPE : false

  const horizon = (
    <div className="seg" role="group" aria-label="Forecast horizon">
      {[1, 2, 3, 4].map(n => (
        <button key={n} aria-pressed={h === n} onClick={() => setH(n)}>
          {n} wk{n > 1 ? 's' : ''} ahead
        </button>
      ))}
    </div>
  )

  return (
    <Page
      kicker="Forecast check"
      title={beats ? 'The festival uplift is earning its place.' : 'The plain average beat the festival uplift.'}
      crumb="Each forecast uses only the weeks before it, then is scored on the week it predicted. Lower error is better."
    >
      <div className="kpis" style={{ ['--n' as string]: 3 }}>
        {ORDER.filter(m => by[m]).map(m => (
          <Kpi
            key={m}
            label={LABEL[m]}
            dot={COLOR[m]}
            value={`${(by[m].WAPE * 100).toFixed(1)}%`}
            note={`MAE ${fmt(by[m].MAE, 1)} units · ${fmt(by[m].observations)} product-weeks`}
            tone={m === 'rules_engine' && !beats ? 'up' : undefined}
          />
        ))}
      </div>

      <div className="grid">
        <Card
          className="span-8"
          title="Error by target week"
          sub="WAPE = total absolute error ÷ total actual units. Lower is better."
          right={horizon}
          foot={<span>{beats ? 'The festival uplift improves accuracy on this sample.' : 'From the first October week, the 25% uplift adds demand that did not arrive for most products.'}</span>}
        >
          <WeekColumns data={bt.by_week} methods={ORDER} colors={COLOR} />
          <div className="legend">
            {ORDER.map(m => (
              <span key={m}>
                <i style={{ background: COLOR[m] }} />
                {LABEL[m]}
              </span>
            ))}
          </div>
        </Card>
        <Card className="span-4" title="Method and limits">
          <ul className="formula">
            {bt.notes.map(n => (
              <li key={n}>{n}</li>
            ))}
            <li>
              {fmt(bt.observations)} predictions evaluated; {fmt(bt.excluded)} origins excluded for having fewer than 12 weeks of history.
            </li>
            <li>15 products × 16 weeks is a small sample. Forecast accuracy is not a rupee outcome; no savings are claimed.</li>
          </ul>
        </Card>
      </div>

      <div className="grid">
        <Card className="span-12" title="Per product" sub="The green dot marks the lowest error for each product." bodyClass="flush">
          <div className="table-scroll">
            <table className="data stack">
              <thead>
                <tr>
                  <th>SKU</th>
                  {ORDER.map(m => (
                    <th key={m} className="r">
                      {LABEL[m]}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {bt.per_sku.map(row => {
                  const best = Math.min(...ORDER.map(m => Number(row[m] ?? 9)))
                  return (
                    <tr key={String(row.sku_id)}>
                      <td className="primary">
                        <strong>{String(row.sku_id)}</strong>
                        <span className="sub">{state.recommendations.find(r => r.sku_id === row.sku_id)?.sku_name.replace('Freshroots ', '')}</span>
                      </td>
                      {ORDER.map(m => (
                        <td key={m} className="r" data-label={LABEL[m]}>
                          {row[m] === undefined || row[m] === null ? '—' : Number(row[m]) === best ? <span className="win">{(Number(row[m]) * 100).toFixed(1)}%</span> : `${(Number(row[m]) * 100).toFixed(1)}%`}
                        </td>
                      ))}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </Page>
  )
}
