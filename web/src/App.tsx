import { useEffect, useState } from 'react'
import { AppProvider } from './ctx'
import { scrollToTop } from './motion'
import { ROUTES, Shell } from './components/Nav'
import { SkuDrawer } from './components/Drawer'
import { Overview } from './pages/Overview'
import { Planning } from './pages/Planning'
import { Exceptions } from './pages/Exceptions'
import { Workbench } from './pages/Workbench'
import { Signals } from './pages/Signals'
import { Backtest } from './pages/Backtest'
import { Data } from './pages/Data'
import { Plan } from './pages/Readiness'

const PAGES: Record<string, () => React.JSX.Element> = {
  '': Overview,
  planning: Planning,
  exceptions: Exceptions,
  workbench: Workbench,
  signals: Signals,
  backtest: Backtest,
  data: Data,
  plan: Plan,
}

const readRoute = () => {
  const raw = window.location.hash.replace(/^#\/?/, '').split(/[?/]/)[0]
  const r = raw === 'readiness' ? 'plan' : raw
  return r in PAGES ? r : ''
}

export default function App() {
  const [route, setRoute] = useState(readRoute)

  useEffect(() => {
    const onHash = () => setRoute(readRoute())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  useEffect(() => {
    scrollToTop()
    const label = ROUTES.find(r => r.path === route)?.label ?? 'The brief'
    document.title = route ? `${label} · Freshroots Planning Brief` : 'Freshroots Planning Brief'
  }, [route])

  const Page = PAGES[route]
  return (
    <AppProvider>
      {(ready, error) =>
        ready ? (
          <Shell route={route}>
            <Page key={route} />
            <SkuDrawer />
          </Shell>
        ) : (
          <div className="loading">
            <div>
              {!error && <div className="pulse" aria-hidden="true" />}
              {error ? (
                <>
                  <p style={{ color: 'var(--ink)', margin: '0 auto 6px' }}>The brief could not reach its data.</p>
                  <p className="fine" style={{ margin: '0 auto', fontStyle: 'normal' }}>
                    {error}. Start the API with python serve.py, then reload.
                  </p>
                </>
              ) : (
                'Setting this week’s brief'
              )}
            </div>
          </div>
        )
      }
    </AppProvider>
  )
}
