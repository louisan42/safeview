import { formatDay } from './dates'

/** Treat published TPS data as stale when the newest report_date is this many calendar days behind UTC today. */
export const PUBLISHED_LAG_DAYS = 14

export function displaySha(apiSha?: string | null, viteSha?: string | null): string {
  const api = (apiSha || '').trim()
  if (api) return api.slice(0, 7)
  const vite = (viteSha || '').trim()
  if (vite) return vite.slice(0, 7)
  return 'dev'
}

export function formatUpdatedLine(lastEtlRunAt?: string | null): string | null {
  const day = formatDay(lastEtlRunAt)
  return day ? `Updated ${day}` : null
}

export function formatAppVersionLine(sha: string): string {
  return `App version: ${sha}`
}

export function formatTpsThroughLine(maxReportDate?: string | null): string | null {
  const day = formatDay(maxReportDate)
  return day ? `TPS data through ${day}` : null
}

export function daysBehindUtc(maxReportDate?: string | null, now = new Date()): number | null {
  if (!maxReportDate) return null
  const day = maxReportDate.slice(0, 10)
  const parsed = new Date(`${day}T00:00:00Z`)
  if (Number.isNaN(parsed.getTime())) return null
  const todayUtc = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate())
  return Math.floor((todayUtc - parsed.getTime()) / 86_400_000)
}

export function publishedLagNote(maxReportDate?: string | null, now = new Date()): string | null {
  const days = daysBehindUtc(maxReportDate, now)
  if (days === null || days < PUBLISHED_LAG_DAYS) return null
  const day = formatDay(maxReportDate)
  if (!day) return null
  return `Incidents follow Toronto Police open data, which can lag (currently through ${day}).`
}

export function deployHoverTitle(deploymentId?: string | null, version?: string | null): string | undefined {
  const parts = [version ? `v${version}` : null, deploymentId ? `deploy ${deploymentId}` : null].filter(Boolean)
  return parts.length ? parts.join(' · ') : undefined
}
