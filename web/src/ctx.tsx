import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { api, type Actor, type Rec, type State } from './api'

type Toast = { text: string; kind: 'ok' | 'error' } | null

type Ctx = {
  state: State
  actor: Actor
  setActor: (name: string) => void
  runId: string
  setRunId: (id: string | null) => void
  refresh: () => Promise<void>
  act: (label: string, fn: () => Promise<unknown>) => Promise<boolean>
  toast: (text: string, kind?: 'ok' | 'error') => void
  openSku: (sku: string | null) => void
  openSkuId: string | null
  recBySku: Map<string, Rec>
}

const AppCtx = createContext<Ctx | null>(null)

export function useApp(): Ctx {
  const c = useContext(AppCtx)
  if (!c) throw new Error('useApp outside provider')
  return c
}

const ACTOR_KEY = 'freshroots.actor'

function readActor(): string | null {
  try {
    return window.localStorage.getItem(ACTOR_KEY)
  } catch {
    return null
  }
}

export function AppProvider({ children }: { children: (ready: boolean, error: string | null) => ReactNode }) {
  const [state, setState] = useState<State | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [runId, setRunIdState] = useState<string | null>(null)
  const [actorName, setActorName] = useState<string>(() => readActor() || 'Raghav Kulkarni')
  const [toastState, setToast] = useState<Toast>(null)
  const [openSkuId, openSku] = useState<string | null>(null)
  const toastTimer = useRef<number | undefined>(undefined)

  const load = useCallback(async (id: string | null) => {
    try {
      const s = await api.state(id || undefined)
      setState(s)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }, [])

  useEffect(() => {
    load(runId)
  }, [load, runId])

  const toast = useCallback((text: string, kind: 'ok' | 'error' = 'ok') => {
    setToast({ text, kind })
    window.clearTimeout(toastTimer.current)
    toastTimer.current = window.setTimeout(() => setToast(null), kind === 'error' ? 5200 : 3200)
  }, [])

  const refresh = useCallback(() => load(runId), [load, runId])

  const act = useCallback(
    async (label: string, fn: () => Promise<unknown>) => {
      try {
        await fn()
        toast(label)
        await load(runId)
        return true
      } catch (e) {
        toast(e instanceof Error ? e.message : String(e), 'error')
        return false
      }
    },
    [load, runId, toast],
  )

  const setActor = useCallback((name: string) => {
    setActorName(name)
    try {
      window.localStorage.setItem(ACTOR_KEY, name)
    } catch {
      /* per-viewer convenience only */
    }
  }, [])

  const value = useMemo<Ctx | null>(() => {
    if (!state) return null
    const actor = state.meta.actors.find(a => a.name === actorName) || state.meta.actors[0]
    return {
      state,
      actor,
      setActor,
      runId: state.meta.run.run_id,
      setRunId: id => setRunIdState(id),
      refresh,
      act,
      toast,
      openSku,
      openSkuId,
      recBySku: new Map(state.recommendations.map(r => [r.sku_id, r])),
    }
  }, [state, actorName, setActor, refresh, act, toast, openSkuId])

  return (
    <>
      {value ? <AppCtx.Provider value={value}>{children(true, error)}</AppCtx.Provider> : children(false, error)}
      <div className={`toast ${toastState ? 'show' : ''} ${toastState?.kind === 'error' ? 'error' : ''}`} role="status" aria-live="polite">
        {toastState?.text}
      </div>
    </>
  )
}
