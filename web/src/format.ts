import type { Rec } from './api'

export const fmt = (x: number | null | undefined, digits = 0) =>
  x === null || x === undefined || Number.isNaN(x) ? '—' : x.toLocaleString('en-IN', { minimumFractionDigits: digits, maximumFractionDigits: digits })

export const pct = (x: number | null | undefined, digits = 1, sign = true) =>
  x === null || x === undefined ? '—' : `${sign && x > 0 ? '+' : ''}${(x * 100).toFixed(digits)}%`

export const cover = (r: Rec) => (r.cover_is_infinite ? 'No demand' : r.weeks_of_cover === null ? '—' : r.weeks_of_cover.toFixed(1))

export const dateLong = (iso: string) =>
  new Date(`${iso}T00:00:00`).toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })

export const monthName = (ym: string) => new Date(`${ym}-01T00:00:00`).toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })

/** Severity of a recommendation for state dots: crit = below minimum cover, warn = above max / conflict. */
export function recState(r: Rec): 'crit' | 'warn' | 'ok' | 'info' {
  const f = r.flags
  if (r.action === 'Planner decision required') return 'info'
  if (f.includes('STOCKOUT_RISK') || f.includes('PERISHABLE_REPLENISH_RISK')) return 'crit'
  if (f.includes('OVERSTOCK_RISK') || f.includes('PERISHABLE_OVERSTOCK_RISK')) return 'warn'
  if (f.includes('HIGH_DEMAND')) return 'warn'
  return 'ok'
}

export function statusState(status: string): 'ok' | 'warn' | 'crit' | 'info' | 'done' | 'neutral' {
  switch (status) {
    case 'Pending planner review':
    case 'Pending procurement approval':
      return 'warn'
    case 'Planner approved':
    case 'Planner overridden':
      return 'info'
    case 'Procurement approved':
      return 'ok'
    case 'Exported as draft':
      return 'done'
    case 'Rejected':
      return 'crit'
    default:
      return 'neutral'
  }
}

export const numberWord = (n: number) =>
  ['No', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Eleven', 'Twelve'][n] ?? String(n)
