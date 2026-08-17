import type { Interval, OverlayMode, TimelinePoint } from './types'

export type ChartSeries = {
  name: string
  values: number[]
  color: string
}

export function alignSeries(
  current: TimelinePoint[],
  prior: TimelinePoint[],
): { labels: string[]; current: number[]; prior: number[] } {
  const n = Math.max(current.length, prior.length)
  const labels: string[] = []
  const currentValues: number[] = []
  const priorValues: number[] = []
  for (let i = 0; i < n; i += 1) {
    labels.push(current[i]?.date || prior[i]?.date || '')
    currentValues.push(current[i]?.count ?? 0)
    priorValues.push(prior[i]?.count ?? 0)
  }
  return { labels, current: currentValues, prior: priorValues }
}

export function categoryRank(key: string): number {
  const lower = key.toLowerCase()
  if (lower.includes('robbery')) return 0
  if (lower.includes('break')) return 1
  if (lower.includes('theft')) return 2
  return 3
}

export function orderedCategoryKeys(records: Array<Record<string, TimelinePoint[] | undefined>>): string[] {
  const keys = new Set<string>()
  for (const record of records) {
    for (const key of Object.keys(record)) {
      if (record[key]?.length) keys.add(key)
    }
  }
  return [...keys].sort((a, b) => categoryRank(a) - categoryRank(b) || a.localeCompare(b))
}

export function seriesForCategory(
  record: Record<string, TimelinePoint[]> | undefined,
  key: string,
): TimelinePoint[] {
  if (!record) return []
  if (record[key]) return record[key]
  const lower = key.toLowerCase()
  const match = Object.keys(record).find((candidate) => candidate.toLowerCase() === lower)
  return match ? record[match] : []
}

export function niceMax(value: number): number {
  if (value <= 0) return 1
  const padded = value * 1.08
  const magnitude = 10 ** Math.floor(Math.log10(padded))
  const normalized = padded / magnitude
  const nice = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10
  return nice * magnitude
}

export function yTicks(max: number, count = 4): number[] {
  const ticks: number[] = []
  for (let i = 0; i <= count; i += 1) {
    ticks.push(Math.round((max * i) / count))
  }
  return [...new Set(ticks)]
}

export function xTickIndexes(length: number): number[] {
  if (length <= 1) return length === 1 ? [0] : []
  if (length <= 5) return Array.from({ length }, (_, i) => i)
  return [0, Math.round((length - 1) / 3), Math.round(((length - 1) * 2) / 3), length - 1]
}

export function overlayCaption(mode: OverlayMode, interval: Interval, xLabel: string): string {
  const y = 'Y: reported incidents'
  const x = `X: ${xLabel}`
  switch (mode) {
    case 'window':
      return `${y} · ${x} · Previous window is the same length, aligned by ${interval}`
    case 'hood':
      return `${y} · ${x} · Same dates and filters for both neighbourhoods`
    default: {
      const _never: never = mode
      return _never
    }
  }
}
