export function isoDateUTC(d: Date): string {
  return d.toISOString().slice(0, 10)
}

export function addDaysIso(iso: string, days: number): string {
  const d = new Date(`${iso}T00:00:00Z`)
  d.setUTCDate(d.getUTCDate() + days)
  return isoDateUTC(d)
}

export function clampDate(iso: string, min: string | null, max: string | null): string {
  if (min && iso < min) return min
  if (max && iso > max) return max
  return iso
}

export function lastNDaysOfData(maxIso: string, n: number, minIso?: string | null): { from: string; to: string } {
  const to = maxIso
  let from = addDaysIso(maxIso, -(n - 1))
  if (minIso && from < minIso) from = minIso
  return { from, to }
}

export function startOfDayZ(dStr: string): string {
  return `${dStr}T00:00:00Z`
}

export function endOfDayZ(dStr: string): string {
  return `${dStr}T23:59:59Z`
}

export function nextDayStartZ(dStr: string): string {
  return `${addDaysIso(dStr, 1)}T00:00:00Z`
}

export function formatDay(iso: string | undefined | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) {
    const dateOnly = iso.slice(0, 10)
    const parsed = new Date(`${dateOnly}T00:00:00Z`)
    if (Number.isNaN(parsed.getTime())) return iso
    return parsed.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })
  }
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })
}

export function windowOverlapsData(from: string, to: string, min: string | null, max: string | null): boolean {
  if (!min || !max) return true
  return !(to < min || from > max)
}
