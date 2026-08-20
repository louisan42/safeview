import { formatDay } from './dates'

export function displaySha(apiSha?: string | null, viteSha?: string | null): string {
  const api = (apiSha || '').trim()
  if (api) return api.slice(0, 7)
  const vite = (viteSha || '').trim()
  if (vite) return vite.slice(0, 7)
  return 'dev'
}

export function formatDataClause(lastEtlRunAt?: string | null, maxReportDate?: string | null): string | null {
  if (lastEtlRunAt) {
    const day = formatDay(lastEtlRunAt)
    return day ? `Data ${day}` : null
  }
  if (maxReportDate) {
    const day = formatDay(maxReportDate)
    return day ? `Latest incident ${day}` : null
  }
  return null
}

export function formatBuildLine(opts: {
  apiSha?: string | null
  viteSha?: string | null
  lastEtlRunAt?: string | null
  maxReportDate?: string | null
}): string {
  const parts = ['Watchtile', displaySha(opts.apiSha, opts.viteSha)]
  const data = formatDataClause(opts.lastEtlRunAt, opts.maxReportDate)
  if (data) parts.push(data)
  return parts.join(' · ')
}
