import { useApp } from '../ctx'
import { Card, Kpi, Page } from '../components/Nav'

export function Plan() {
  const { state } = useApp()
  const R = state.readiness
  const span = 90

  return (
    <Page title="Plan" crumb="What the rollout could be worth, how it runs, and what Freshroots still has to confirm.">
      <div className="kpis" style={{ ['--n' as string]: 3 }}>
        <Kpi label="Reported losses" value="₹28–34L" note="per quarter, from the case" />
        <Kpi label="Budget" value="₹15L" note="treated as a one-time cost" />
        <Kpi label="Rollout" value="90 days" note="six phases, ending in a pilot" />
      </div>

      <div className="grid">
        <Card className="span-12" title="If it works" sub="Scenarios only. Reduction percentages are assumptions; nothing has been realised or measured." bodyClass="flush">
          <div className="table-scroll">
            <table className="data stack">
              <thead>
                <tr>
                  {Object.keys(R.roi[0] ?? {}).map(k => (
                    <th key={k} className={k.startsWith('Assumed') ? undefined : 'r'}>
                      {k}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {R.roi.map((row, i) => (
                  <tr key={i}>
                    {Object.entries(row).map(([k, v]) => (
                      <td key={k} className={k.startsWith('Assumed') ? 'primary' : 'r'} data-label={k.startsWith('Assumed') ? undefined : k}>
                        {k.startsWith('Assumed') ? <strong>{v} reduction</strong> : v}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      <div className="grid">
        <Card className="span-7" title="Ninety days" sub="A proposed plan. It moves with data access and data quality.">
          <div className="timeline">
            {R.plan.map(p => (
              <div className="timeline-row" key={p.Phase}>
                <div>
                  <div style={{ fontWeight: 600 }}>{p.Phase}</div>
                  <div className="fine">
                    Days {p['Start day']}–{p['End day']}
                  </div>
                </div>
                <div>
                  <div className="timeline-track" aria-hidden="true">
                    <div className="timeline-seg" style={{ left: `${((p['Start day'] - 1) / span) * 100}%`, width: `${((p['End day'] - p['Start day'] + 1) / span) * 100}%` }} />
                  </div>
                  <p className="small muted" style={{ margin: '6px 0 0' }}>
                    {p.Work}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Card>
        <Card className="span-5" title="Still open" sub="Each has a labelled prototype assumption until Raghav and procurement confirm it.">
          <ul className="list">
            {R.open_questions.map(q => (
              <li key={q}>
                <span className="small">{q}</span>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </Page>
  )
}
