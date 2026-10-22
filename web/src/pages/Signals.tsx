import { useApp } from '../ctx'
import { Card, Kpi, Page } from '../components/Nav'
import { SignalStrip } from '../components/Charts'
import { Triage } from '../components/Decide'
import { pct } from '../format'

export function Signals() {
  const { state } = useApp()
  const sig = state.signals
  const open = sig.filter(s => s.status === 'New' || s.status === 'Surfaced to procurement')
  const hist = state.signal_history
  const weeks = [...new Set(state.weekly.map(w => w.week))].sort()
  const skus = [...new Set(hist.map(h => h.sku_id))].sort()
  const t = state.meta.thresholds

  return (
    <Page title="Signals" crumb="Weekly sales movements routed to Priya, then acknowledged by procurement before any order for that SKU.">
      <div className="kpis" style={{ ['--n' as string]: 4 }}>
        <Kpi label={`Open in ${state.meta.anchor_week}`} value={open.length} tone={open.length ? 'warn' : 'good'} note={open.length ? 'Orders for these SKUs are held' : 'No order line is held'} />
        <Kpi label="Detected in history" value={hist.length} note={skus.join(', ') || 'None'} />
        <Kpi label="Drop threshold" value={`${Math.round(t.signal_drop * 100)}%`} note="vs previous 4 weeks or week on week" />
        <Kpi label="Spike threshold" value={`${Math.round(t.signal_spike * 100)}%`} note="Proposed, to agree with Priya" />
      </div>

      <div className="grid">
        <Card className="span-7" title="This week's pulse" sub="The part of the 12-metric Monday report this data supports" bodyClass="flush">
          <div className="table-scroll">
            <table className="data stack">
              <thead>
                <tr>
                  <th>Metric</th>
                  <th className="r">Latest</th>
                  <th className="r">Previous</th>
                  <th className="r">Change</th>
                </tr>
              </thead>
              <tbody>
                {state.pulse.map(p => (
                  <tr key={p.Metric}>
                    <td className="primary">
                      <strong>{p.Metric}</strong>
                      <span className="sub">{p.Basis}</span>
                    </td>
                    <td className="r" data-label="Latest">
                      {p.Latest}
                    </td>
                    <td className="r" data-label="Previous">
                      {p.Previous}
                    </td>
                    <td className="r" data-label="Change">
                      {p.Change}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
        <Card className="span-5" title="Report coverage" sub="What the full 12-metric report would need">
          <ul className="list">
            {state.metric_catalog.map(m => (
              <li key={m.metric}>
                <span>
                  {m.metric}
                  <span className="fine" style={{ display: 'block' }}>
                    {m.note}
                  </span>
                </span>
                <span className={`tag ${m.availability === 'Available' ? 'ok' : m.availability.startsWith('Proxy') ? 'warn' : ''}`}>{m.availability}</span>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      {sig.length > 0 && (
        <div className="grid">
          {sig.map(s => (
            <Card key={s.sid} className="span-6" title={`${s.sku_id} · ${s.signal_type.replaceAll('_', ' ').toLowerCase()}`} sub={`${s.week} · ${s.severity}`} right={<span className="kpi-value" style={{ fontSize: 20 }}>{pct(s.change_pct)}</span>}>
              <p className="small muted">{s.message}</p>
              <Triage signal={s} />
            </Card>
          ))}
        </div>
      )}

      <div className="grid">
        <Card className="span-12" title="Every week, scanned" sub="Signals the monitor would have raised in earlier weeks. Only the latest week is routed for action.">
          {hist.length ? <SignalStrip weeks={weeks} signals={hist} skus={skus} /> : <p className="empty">No signals in the history at these thresholds.</p>}
          <div className="legend">
            <span>
              <i style={{ background: '#dc2626' }} />
              Drop vs trend
            </span>
            <span>
              <i style={{ background: '#d97706' }} />
              Week-on-week drop
            </span>
            <span>
              <i style={{ background: '#334155' }} />
              Spike vs trend
            </span>
          </div>
          {hist.length > 0 && (
            <ul className="list" style={{ marginTop: 10 }}>
              {hist.map(h => (
                <li key={h.signal_id}>
                  <span>
                    <strong>
                      {h.week} · {h.sku_id}
                    </strong>{' '}
                    <span className="muted">{h.message}</span>
                  </span>
                  <span className="num">{pct(h.change_pct)}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </Page>
  )
}
