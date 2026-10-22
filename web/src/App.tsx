import { useEffect, useState } from 'react'
import { AppProvider } from './ctx'
import { useCardEntrance, useScrollRefresh, useSmoothScroll, scrollToTop } from './motion'
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

function Routed({ route }: { route: string }) {
  const Page = PAGES[route]
  useCardEntrance(route)
  return (
    <Shell route={route}>
      <Page key={route} />
      <SkuDrawer />
    </Shell>
  )
}

export default function App() {
  const [route, setRoute] = useState(readRoute)
  useSmoothScroll()
  useScrollRefresh()

  useEffect(() => {
    const onHash = () => setRoute(readRoute())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  useEffect(() => {
    scrollToTop()
    const label = ROUTES.find(r => r.path === route)?.label ?? 'Overview'
    document.title = route ? `${label} · Freshroots Planner` : 'Freshroots Planner'
  }, [route])

  return (
    <AppProvider>
      {(ready, error) =>
        ready ? (
          <Routed route={route} />
        ) : (
          <div className="loading">
            <div>
              {!error && <div className="pulse" aria-hidden="true" />}
              {error ? (
                <>
                  <p style={{ color: 'var(--ink)', fontSize: 16, fontWeight: 600, margin: '0 auto 6px' }}>The planner could not reach its data.</p>
                  <p style={{ margin: '0 auto' }}>{error}. Start the API with python serve.py, then reload.</p>
                </>
              ) : (
                'Loading the latest run'
              )}
            </div>
          </div>
        )
      }
    </AppProvider>
  )
}
