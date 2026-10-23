import { useState } from 'react'
import { Download } from 'lucide-react'
import { useApp } from '../ctx'
import { Card, Kpi, Page } from '../components/Nav'
import { fmt, numberWord } from '../format'

const SEV = ['error', 'warning', 'info'] as const

export function Data() {
  const { state } = useApp()
  const q = state.quality
  const [sev, setSev] = useState<string>('all')
  const files = Object.values(q.summaries)
  const issues = q.issues.filter(i => sev === 'all' || i.severity === sev)
  const rows = files.reduce((s, f) => s + f.rows, 0)
  const excluded = files.reduce((s, f) => s + (f.rows_excluded ?? 0), 0)

  return (
    <Page
      kicker="Data"
      title={`${numberWord(files.length)} files, checked before any rule runs.`}
      crumb="Every file is read as text and validated first. Nothing is dropped silently, and what the data cannot show is stated, never guessed."
      action={
        <a className="btn btn-secondary" href="/api/validation.csv">
          <Download size={15} /> Findings CSV
        </a>
      }
    >
      <div className="kpis" style={{ ['--n' as string]: 4 }}>
        <Kpi label="Errors" value={q.errors} tone={q.errors ? 'bad' : 'good'} note={q.errors ? 'Rows excluded and listed' : 'All rows usable'} />
        <Kpi label="Warnings" value={q.warnings} tone={q.warnings ? 'warn' : 'good'} />
        <Kpi label="Rows checked" value={fmt(rows)} note={`${files.length} files`} />
        <Kpi label="Rows excluded" value={excluded} />
      </div>

      <div className="grid">
        <Card className="span-12" title="Files" bodyClass="flush">
          <div className="table-scroll">
            <table className="data stack">
              <thead>
                <tr>
                  <th>File</th>
                  <th>Status</th>
                  <th className="r">Rows</th>
                  <th className="r">Excluded</th>
                  <th className="r">Products</th>
                  <th className="r">Distributors</th>
                  <th>Range</th>
                </tr>
              </thead>
              <tbody>
                {files.map(f => {
                  const fi = q.issues.filter(i => i.file === f.file)
                  const e = fi.filter(i => i.severity === 'error').length
                  const w = fi.filter(i => i.severity === 'warning').length
                  return (
                    <tr key={f.file}>
                      <td className="primary">
                        <strong>{f.file}</strong>
                        <span className="sub">{Object.keys(f.columns).join(', ')}</span>
                      </td>
                      <td data-label="Status">
                        <span className={`state ${e ? 'crit' : w ? 'warn' : 'ok'}`}>{e ? `${e} errors` : w ? `${w} warnings` : 'Valid'}</span>
                      </td>
                      <td className="r" data-label="Rows">
                        {fmt(f.rows)}
                      </td>
                      <td className="r" data-label="Excluded">
                        {fmt(f.rows_excluded ?? 0)}
                      </td>
                      <td className="r hide-sm">{f.unique_skus ?? '—'}</td>
                      <td className="r hide-sm">{f.unique_distributors ?? '—'}</td>
                      <td className="small hide-sm">{f.date_range ?? '—'}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      <div className="grid">
        <Card
          className="span-8"
          title="Findings"
          right={
            <div className="seg" role="group" aria-label="Severity">
              {['all', ...SEV].map(s => (
                <button key={s} aria-pressed={sev === s} onClick={() => setSev(s)}>
                  {s === 'all' ? 'All' : `${s[0].toUpperCase()}${s.slice(1)}s`}
                </button>
              ))}
            </div>
          }
          bodyClass="flush"
        >
          <div className="table-scroll">
            <table className="data stack">
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>File</th>
                  <th className="r">Line</th>
                  <th>Finding</th>
                </tr>
              </thead>
              <tbody>
                {issues.map((i, n) => (
                  <tr key={n}>
                    <td data-label="Severity">
                      <span className={`state ${i.severity === 'error' ? 'crit' : i.severity === 'warning' ? 'warn' : 'neutral'}`}>{i.severity}</span>
                    </td>
                    <td className="small" data-label="File">
                      {i.file}
                    </td>
                    <td className="r" data-label="Line">
                      {i.line ?? '—'}
                    </td>
                    <td className="small muted primary">
                      <strong style={{ color: 'var(--ink)' }}>{i.check.replaceAll('_', ' ')}</strong>
                      {i.value ? ` · ${i.value}` : ''}
                      <span className="sub">{i.message}</span>
                    </td>
                  </tr>
                ))}
                {!issues.length && (
                  <tr>
                    <td colSpan={4} className="empty">
                      No findings at this severity.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
        <Card className="span-4" title="What the data cannot show" sub="Stated, never filled in with guesses">
          <ul className="list">
            <li>
              <span>Distributor-level sales</span>
              <span className="tag">Not in data</span>
            </li>
            <li>
              <span>Lead times and open POs</span>
              <span className="tag">Not in data</span>
            </li>
            <li>
              <span>Expiry and shelf life</span>
              <span className="tag">Not in data</span>
            </li>
            <li>
              <span>Prices and costs</span>
              <span className="tag">Not in data</span>
            </li>
            <li>
              <span>Suppliers</span>
              <span className="tag">Not in data</span>
            </li>
            <li>
              <span>
                Scale: {state.recommendations.length} products, {new Set(state.weekly.map(w => w.week)).size} weeks
              </span>
              <span className="tag warn">Sample</span>
            </li>
          </ul>
        </Card>
      </div>

      <div className="grid">
        <Card className="span-12" title={`Data dictionary · ${q.dictionary.length} columns`} bodyClass="flush">
          <details className="disclose">
            <summary>Show columns</summary>
            <div className="table-scroll">
              <table className="data stack">
                <thead>
                  <tr>
                    <th>File</th>
                    <th>Column</th>
                    <th>Type</th>
                    <th className="r">Missing</th>
                    <th>Example</th>
                    <th>Meaning</th>
                  </tr>
                </thead>
                <tbody>
                  {q.dictionary.map(d => (
                    <tr key={`${d.file}-${d.column}`}>
                      <td className="small" data-label="File">
                        {d.file}
                      </td>
                      <td className="primary">
                        <strong>{d.column}</strong>
                      </td>
                      <td className="small" data-label="Type">
                        {d.observed_type}
                      </td>
                      <td className="r" data-label="Missing">
                        {d.missing}
                      </td>
                      <td className="small" data-label="Example">
                        {d.example}
                      </td>
                      <td className="small muted primary">{d.description}</td>
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
