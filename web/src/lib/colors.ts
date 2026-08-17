/** UI chrome (buttons, chips, focus, selection). Not crime density. */
export const ACCENT = '#2563EB'
/** Current window / neighbourhood A on charts. Same blue as UI chrome. */
export const CHART_CURRENT = ACCENT
/** Previous window / neighbourhood B / theft-over series. */
export const CHART_PRIOR = '#475569'
/** Break-and-enter series. Warm, not choropleth orange or crime red. */
export const CHART_BNE = '#B45309'
export const CHART_OTHER = '#64748B'

export function categorySeriesColor(raw: string): string {
  const lower = raw.toLowerCase()
  if (lower.includes('robbery')) return CHART_CURRENT
  if (lower.includes('break')) return CHART_BNE
  if (lower.includes('theft')) return CHART_PRIOR
  return CHART_OTHER
}
export const ACCENT_STRONG = '#1D4ED8'
export const ACCENT_SOFT = '#DBEAFE'
/** Choropleth high / map clusters. Keep yellow→red ramp off the UI accent. */
export const CRIME_HIGH = '#E11D48'

export function colorForIncident(f: { properties?: { mci_category?: string; dataset?: string } } | null | undefined): string {
  const key = (f?.properties?.mci_category || f?.properties?.dataset || '').toLowerCase()
  if (key.includes('robbery')) return '#DC2626'
  if (key.includes('assault')) return '#2563EB'
  if (key.includes('theft')) return '#EAB308'
  if (key.includes('break') || key.includes('enter')) return '#F97316'
  if (key.includes('auto') || key.includes('vehicle')) return '#C026D3'
  return '#64748B'
}

/** Sequential yellow → orange → red. Low count is yellow, high is red. */
export const CHOROPLETH_RAMP = ['#FDE047', '#FACC15', '#FB923C', '#F97316', CRIME_HIGH] as const

export function choroplethColor(count: number, max: number): string {
  if (!count || max <= 0) return CHOROPLETH_RAMP[0]
  const t = count / max
  if (t <= 0.2) return CHOROPLETH_RAMP[0]
  if (t <= 0.4) return CHOROPLETH_RAMP[1]
  if (t <= 0.6) return CHOROPLETH_RAMP[2]
  if (t <= 0.8) return CHOROPLETH_RAMP[3]
  return CHOROPLETH_RAMP[4]
}

export function choroplethOpacity(count: number): number {
  return count > 0 ? 0.62 : 0.38
}
