import type { DatasetKey, TimePreset } from './types'

export function datasetLabel(key: string | null | undefined): string {
  const k = (key || '').toLowerCase()
  switch (k) {
    case 'robbery':
      return 'Robbery'
    case 'theft_over':
      return 'Theft over $5,000'
    case 'break_and_enter':
      return 'Break and enter'
    case '':
      return 'All categories'
    default:
      return humanizeToken(key || '')
  }
}

export function categoryLabel(raw: string | null | undefined): string {
  const v = (raw || '').trim()
  if (!v) return 'Incident'
  const lower = v.toLowerCase()
  switch (lower) {
    case 'theft over':
    case 'theft_over':
      return 'Theft over $5,000'
    case 'break and enter':
    case 'break_and_enter':
      return 'Break and enter'
    case 'robbery':
      return 'Robbery'
    default:
      return v
  }
}

export function humanizeToken(value: string): string {
  return value
    .replace(/_/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

export function timePresetLabel(preset: TimePreset): string {
  switch (preset) {
    case '7d':
      return 'Last 7d'
    case '30d':
      return 'Last 30d'
    case '90d':
      return 'Last 90d'
    case 'custom':
      return 'Custom'
    default: {
      const _never: never = preset
      return _never
    }
  }
}

export function timePresetDays(preset: TimePreset): number | null {
  switch (preset) {
    case '7d':
      return 7
    case '30d':
      return 30
    case '90d':
      return 90
    case 'custom':
      return null
    default: {
      const _never: never = preset
      return _never
    }
  }
}

export const DATASET_OPTIONS: Array<{ value: '' | DatasetKey; label: string }> = [
  { value: '', label: 'All' },
  { value: 'robbery', label: datasetLabel('robbery') },
  { value: 'theft_over', label: datasetLabel('theft_over') },
  { value: 'break_and_enter', label: datasetLabel('break_and_enter') },
]
