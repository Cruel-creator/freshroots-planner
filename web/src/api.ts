// Typed client for the Python API (freshroots/api.py).

export type Actor = { name: string; role: 'planner' | 'procurement' | 'analyst' | 'viewer' }

export type Rec = {
  rec_id: string
  run_id: string
  sku_id: string
  sku_name: string
  category: string
  perishability: string
  is_perishable: boolean | null
  unit: string
  mapped_distributor: string
  scope: string
  recent_4w_units: number | null
  recent_4w_avg: number | null
  baseline_12w_avg: number | null
  demand_change_pct: number | null
  demand_basis: number | null
  demand_basis_note: string
  festival_uplift_applied: boolean
  festival_weeks_in_baseline: number
  adjusted_weekly_demand: number | null
  current_stock: number | null
  inventory_as_of: string | null
  weeks_of_cover: number | null
  cover_is_infinite: boolean
  flags: string[]
  flag_reasons: string[]
  conflicts: string[]
  action: string
  priority_step: string
  standard_qty: number | null
  recommended_qty: number | null
  qty_basis: string
  projected_cover_after_order: number | null
  max_qty_within_window: number | null
  shortfall_to_min_cover_units: number | null
  excess_over_max_cover_units: number | null
  needs_review: boolean
  review_reasons: string[]
  data_quality_status: string
  explanation: string
  source_weeks: string[]
  rule_version: string
  exception_codes: string[]
  planning_month: string
  status: string
  planner_decision: string | null
  planner_reason: string | null
  final_action: string | null
  final_qty: number | null
  checkpoints: string[]
}

export type Exception = {
  sku_id: string
  code: string
  category: string
  signal: string
  source_data: string
  rules_triggered: string
  why_not_automated: string
  suggested_action: string
  assigned_to: string
}

export type Weekly = { SKU_ID: string; week: string; week_start: string; units: number; month: string; is_festival: boolean | null }

export type Signal = {
  sid?: string
  signal_id: string
  sku_id: string
  week: string
  signal_type: string
  latest_units: number
  reference_units: number
  change_pct: number
  severity: string
  message: string
  is_latest_week: boolean
  status?: string
  decision?: string | null
  note?: string | null
}

export type Issue = { file: string; line: number | null; column: string | null; severity: string; check: string; value: string | null; message: string; excluded: boolean }

export type BacktestPayload = {
  summary: { method: string; observations: number; MAE: number; WAPE: number; description: string }[]
  by_week: { target: string; target_festival: boolean; method: string; observations: number; MAE: number; WAPE: number }[]
  per_sku: Record<string, string | number>[]
  methods: Record<string, string>
  notes: string[]
  excluded: number
  observations: number
}

export type State = {
  meta: {
    analysis_date: string
    anchor_week: string
    window: string[]
    planning_month: string
    planning_month_festival: boolean | null
    rule_version: string
    run: { run_id: string; created_at: string; created_by: string; rule_version: string }
    runs: { run_id: string; created_at: string; created_by: string }[]
    inputs_changed: boolean
    thresholds: Record<string, number>
    flag_labels: Record<string, string>
    actions: string[]
    review_action: string
    reorder_actions: string[]
    statuses: string[]
    signal_statuses: string[]
    signal_decisions: string[]
    actors: Actor[]
    min_reason: number
    llm_provider: string
  }
  recommendations: Rec[]
  exceptions: Exception[]
  weekly: Weekly[]
  signals: Signal[]
  signal_history: Signal[]
  pulse: { Metric: string; Latest: string; Previous: string; Change: string; Basis: string }[]
  metric_catalog: { metric: string; availability: string; note: string }[]
  quality: {
    summaries: Record<string, { file: string; rows: number; rows_excluded?: number; duplicate_rows: number; unique_skus?: number; unique_distributors?: number; date_range?: string; columns: Record<string, string> }>
    issues: Issue[]
    errors: number
    warnings: number
    dictionary: { file: string; column: string; observed_type: string; missing: number; unique_values: number | null; example: string; description: string }[]
    hashes: Record<string, string>
  }
  backtest: BacktestPayload
  readiness: {
    roi: Record<string, string>[]
    plan: { 'Start day': number; 'End day': number; Phase: string; Work: string }[]
    open_questions: string[]
    priority_steps: { step: string; rule: string }[]
  }
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      if (body?.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      /* keep the status text */
    }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

const post = <T,>(url: string, body: unknown) =>
  request<T>(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })

export const api = {
  state: (runId?: string) => request<State>(`/api/state${runId ? `?run_id=${encodeURIComponent(runId)}` : ''}`),
  backtest: (h: number) => request<BacktestPayload>(`/api/backtest?h=${h}`),
  aiNotes: () =>
    request<{ enabled: boolean; provider: string; model?: string | null; error?: string; notes: { sku_id: string; code: string; note: string; category: string }[] }>(
      '/api/ai-notes',
    ),
  events: (runId: string) => request<Record<string, string | null>[]>(`/api/events?run_id=${encodeURIComponent(runId)}`),
  newRun: (actor: string) => post<{ run_id: string }>('/api/runs', { actor }),
  approve: (recId: string, actor: string) => post(`/api/recs/${encodeURIComponent(recId)}/approve`, { actor }),
  override: (recId: string, actor: string, action: string, qty: number | null, reason: string) =>
    post(`/api/recs/${encodeURIComponent(recId)}/override`, { actor, action, qty, reason }),
  reject: (recId: string, actor: string, reason: string) => post(`/api/recs/${encodeURIComponent(recId)}/reject`, { actor, reason }),
  procure: (recId: string, actor: string) => post(`/api/recs/${encodeURIComponent(recId)}/procure`, { actor }),
  bulkApprove: (runId: string, actor: string) =>
    post<{ approved: number; errors: string[] }>(`/api/runs/${encodeURIComponent(runId)}/bulk-approve`, { actor }),
  draftPo: (runId: string, actor: string) =>
    post<{ rows: Record<string, string | number>[]; csv: string; id: string }>(`/api/runs/${encodeURIComponent(runId)}/draft-po`, { actor }),
  surface: (sid: string, actor: string, reason: string) => post(`/api/signals/${encodeURIComponent(sid)}/surface`, { actor, reason }),
  dismiss: (sid: string, actor: string, reason: string) => post(`/api/signals/${encodeURIComponent(sid)}/dismiss`, { actor, reason }),
  acknowledge: (sid: string, actor: string, decision: string, note: string) =>
    post(`/api/signals/${encodeURIComponent(sid)}/acknowledge`, { actor, decision, note }),
  csv: {
    recommendations: (runId: string) => `/api/runs/${encodeURIComponent(runId)}/recommendations.csv`,
    audit: (runId: string) => `/api/runs/${encodeURIComponent(runId)}/audit.csv`,
    validation: () => '/api/validation.csv',
  },
}

export function downloadText(name: string, text: string) {
  const blob = new Blob([text], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = name
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
