export type DatasetKey = 'robbery' | 'theft_over' | 'break_and_enter'
export type TimePreset = '7d' | '30d' | '90d' | 'custom'
export type Interval = 'day' | 'week' | 'month'
export type Scope = 'map' | 'city'

export type GeoJSONGeometry = {
  type: string
  coordinates: unknown
}

export type IncidentProperties = {
  id: number | string
  dataset?: string
  event_unique_id?: string
  report_date?: string
  report_datetime?: string
  occ_date?: string
  offence?: string
  mci_category?: string
  hood_158?: string
  lon?: number
  lat?: number
}

export type IncidentFeature = {
  type: 'Feature'
  geometry: GeoJSONGeometry | null
  properties: IncidentProperties
}

export type IncidentCollection = {
  type: 'FeatureCollection'
  features: IncidentFeature[]
  total?: number
}

export type NeighbourhoodProperties = {
  area_long_code: string
  area_short_code?: string
  area_name: string
  incident_count?: number
}

export type NeighbourhoodFeature = {
  type: 'Feature'
  geometry: GeoJSONGeometry | null
  properties: NeighbourhoodProperties
}

export type NeighbourhoodCollection = {
  type: 'FeatureCollection'
  features: NeighbourhoodFeature[]
  total?: number
}

export type StatsResponse = {
  total_incidents: number
  min_report_date: string | null
  max_report_date: string | null
  last_etl_run_at: string | null
  by_dataset: Array<{ key: string | null; count: number }>
  by_mci_category: Array<{ key: string | null; count: number }>
}

export type TimelinePoint = {
  date: string
  count: number
}

export type AnalyticsResponse = {
  totals: {
    total: number
    by_dataset: Record<string, number>
    by_category: Record<string, number>
  }
  timeline: TimelinePoint[]
  timeline_by_category?: Record<string, TimelinePoint[]>
}

export type CompareResponse = {
  window_a: AnalyticsResponse
  window_b: AnalyticsResponse
  delta_total: number
  delta_total_pct: number | null
}

export type GeocodeHit = {
  label: string
  lat: number
  lng: number
}

export type NeighbourhoodMatch = {
  area_long_code: string
  area_short_code?: string
  area_name: string
}

export type Delta = {
  diff: number
  pct: number | null
}

export type OverlayMode = 'window' | 'hood'

export type HoodCompare = {
  a: {
    code: string
    name: string
    total: number
    timeline: TimelinePoint[]
    timeline_by_category: Record<string, TimelinePoint[]>
  }
  b: {
    code: string
    name: string
    total: number
    timeline: TimelinePoint[]
    timeline_by_category: Record<string, TimelinePoint[]>
  }
  diff: number
  pct: number | null
}
