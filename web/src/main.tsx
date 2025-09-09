import React from 'react'
import './index.css'
import { createRoot } from 'react-dom/client'
import { MapContainer, TileLayer, GeoJSON, Marker, Popup, ZoomControl, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import { Drawer } from './components/Drawer'
import { Sparkline } from './components/Sparkline'
import { IconButton } from './components/IconButton'
import { Badge } from './components/Badge'
import { MiniBars } from './components/MiniBars'
import { Tooltip } from './components/Tooltip'
import { SearchableSelect } from './components/SearchableSelect'

const API_BASE: string = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8888'

// Sparkline now a reusable component

function App() {
  const [features, setFeatures] = React.useState<any[]>([])
  const [neigh, setNeigh] = React.useState<any | null>(null)
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [dataset, setDataset] = React.useState<string>('')
  // Initialize to last 7 days
  const todayIso = React.useMemo(() => new Date().toISOString().slice(0, 10), [])
  const weekAgoIso = React.useMemo(() => {
    const d = new Date()
    d.setDate(d.getDate() - 7)
    return d.toISOString().slice(0, 10)
  }, [])
  const [dateFrom, setDateFrom] = React.useState<string>(weekAgoIso)
  const [dateTo, setDateTo] = React.useState<string>(todayIso)
  // offence filter removed
  const [citywide, setCitywide] = React.useState<boolean>(false)
  const [drawerOpen, setDrawerOpen] = React.useState<boolean>(true)
  const [statsMaxDate, setStatsMaxDate] = React.useState<string | null>(null)
  const [statsMinDate, setStatsMinDate] = React.useState<string | null>(null)
  const [lastEtlRunAt, setLastEtlRunAt] = React.useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = React.useState<string | null>(null)
  const [statsLoading, setStatsLoading] = React.useState<boolean>(false)
  const mapRef = React.useRef<L.Map | null>(null)
  const lastQueryRef = React.useRef<string>('')
  const fetchTimerRef = React.useRef<number | null>(null)
  const abortRef = React.useRef<AbortController | null>(null)
  const neighCacheRef = React.useRef<Map<string, any>>(new Map())
  const [analytics, setAnalytics] = React.useState<{ total: number; by_category: Record<string, number>; timeline: Array<{ date: string; count: number }> } | null>(null)
  const [delta, setDelta] = React.useState<{ diff: number; pct: number | null } | null>(null)
  const [interval, setInterval] = React.useState<'day' | 'week' | 'month'>('day')
  const lastAnalyticsQueryRef = React.useRef<string>('')
  const lastCompareQueryRef = React.useRef<string>('')
  const analyticsAbortRef = React.useRef<AbortController | null>(null)
  const compareAbortRef = React.useRef<AbortController | null>(null)
  // Neighbourhood compare state
  const [hoodA, setHoodA] = React.useState<string>('')
  const [hoodB, setHoodB] = React.useState<string>('')
  const [hoodCompare, setHoodCompare] = React.useState<null | { a: { name: string; total: number }, b: { name: string; total: number }, diff: number, pct: number | null }>(null)

  const colorFor = (f: any) => {
    const key = (f?.properties?.mci_category || f?.properties?.dataset || '').toLowerCase()
    if (key.includes('robbery')) return '#e11d48'
    // Change assault color to avoid clashing with robbery (was red)
    if (key.includes('assault')) return '#0ea5e9'
    if (key.includes('theft')) return '#f59e0b'
    if (key.includes('break') || key.includes('enter')) return '#8b5cf6'
    if (key.includes('auto') || key.includes('vehicle')) return '#06b6d4'
    return '#22c55e'
  }

  // Build date strings for API consumption
  const startOfDayZ = (dStr: string) => `${dStr}T00:00:00Z`
  const endOfDayZ = (dStr: string) => `${dStr}T23:59:59Z`
  const nextDayStartZ = (dStr: string) => {
    const d = new Date(dStr + 'T00:00:00Z')
    d.setUTCDate(d.getUTCDate() + 1)
    return d.toISOString().slice(0, 19) + 'Z'
  }

  const iconFor = (f: any) => {
    const color = colorFor(f)
    const html = `<span style="display:inline-block;width:14px;height:14px;border-radius:50%;background:${color};box-shadow:0 0 0 2px #fff, 0 0 4px rgba(0,0,0,.3);"></span>`
    return L.divIcon({ className: 'sv-pin', html, iconSize: [14, 14], iconAnchor: [7, 7] })
  }

  const getQuantizedBbox = (map: L.Map) => {
    const b = map.getBounds()
    const q = (n: number) => Number(n.toFixed(4))
    return `${q(b.getWest())},${q(b.getSouth())},${q(b.getEast())},${q(b.getNorth())}`
  }

  const fetchNeighbourhoods = async () => {
    const map = mapRef.current
    if (!map) return
    const b = map.getBounds()
    // Quantize bbox to reduce tiny changes causing refetch
    const q = (n: number) => Number(n.toFixed(4))
    const bbox = `${q(b.getWest())},${q(b.getSouth())},${q(b.getEast())},${q(b.getNorth())}`
    try {
      const res = await fetch(`${API_BASE}/v1/neighbourhoods?limit=5000&bbox=${bbox}`)
      const fc = await res.json()
      if (Array.isArray(fc?.features)) {
        const cache = neighCacheRef.current
        let changed = false
        for (const feat of fc.features) {
          const code = feat?.properties?.area_long_code || feat?.properties?.area_short_code || JSON.stringify(feat?.properties)
          if (code && !cache.has(code)) {
            cache.set(code, feat)
            changed = true
          }
        }
        if (changed) {
          setNeigh({ type: 'FeatureCollection', features: Array.from(cache.values()) })
        } else if (!neigh) {
          // initialize if empty
          setNeigh({ type: 'FeatureCollection', features: Array.from(cache.values()) })
        }
      }
    } catch (e) {
      console.error(e)
    }
  }

  const fetchIncidents = () => {
    const map = mapRef.current
    if (!map) return
    const params = new URLSearchParams()
    params.set('limit', '500')
    if (!citywide) {
      const b = map.getBounds()
      params.set('bbox', `${b.getWest()},${b.getSouth()},${b.getEast()},${b.getNorth()}`)
    }
    if (dataset) params.set('dataset', dataset)
    if (selectedCategory) params.set('mci_category', selectedCategory)
    if (dateFrom) params.set('date_from', startOfDayZ(dateFrom))
    if (dateTo) params.set('date_to', endOfDayZ(dateTo))
    const query = params.toString()
    if (query === lastQueryRef.current) {
      return // no change in query; skip
    }
    lastQueryRef.current = query
    setLoading(true)
    setError(null)
    // Abort any in-flight request
    if (abortRef.current) abortRef.current.abort()
    const controller = new AbortController()
    abortRef.current = controller
    fetch(`${API_BASE}/v1/incidents?${query}`, { signal: controller.signal })
      .then(r => r.json())
      .then(fc => setFeatures(fc.features || []))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false))
  }

  const fetchAnalytics = () => {
    const map = mapRef.current
    if (!map) return
    const params = new URLSearchParams()
    params.set('date_from', startOfDayZ(dateFrom))
    // exclusive end for analytics: next day start
    params.set('date_to', nextDayStartZ(dateTo))
    params.set('interval', interval)
    if (!citywide) params.set('bbox', getQuantizedBbox(map))
    if (dataset) params.set('dataset', dataset)
    if (selectedCategory) params.set('mci_category', selectedCategory)
    const query = params.toString()
    if (query === lastAnalyticsQueryRef.current) return
    lastAnalyticsQueryRef.current = query
    if (analyticsAbortRef.current) analyticsAbortRef.current.abort()
    const controller = new AbortController()
    analyticsAbortRef.current = controller
    fetch(`${API_BASE}/v1/analytics?${query}`, { signal: controller.signal })
      .then(r => r.json())
      .then((data) => {
        const timeline = (data?.timeline || []).map((p: any) => ({ date: p.date, count: p.count }))
        const byCat = data?.totals?.by_category || {}
        const total = Number(data?.totals?.total || 0)
        setAnalytics({ total, by_category: byCat, timeline })
      })
      .catch(() => { /* non-fatal for UI */ })
  }

  const fetchCompare = () => {
    const map = mapRef.current
    if (!map) return
    // Compute previous window same length immediately preceding [date_from, date_to)
    const start = new Date(startOfDayZ(dateFrom))
    // exclusive end = next day start
    const end = new Date(nextDayStartZ(dateTo))
    const ms = end.getTime() - start.getTime()
    const prevEnd = new Date(start.getTime())
    const prevStart = new Date(start.getTime() - ms)
    const fmt = (d: Date) => d.toISOString()
    const params = new URLSearchParams()
    params.set('a_date_from', fmt(start))
    params.set('a_date_to', fmt(end))
    params.set('b_date_from', fmt(prevStart))
    params.set('b_date_to', fmt(prevEnd))
    params.set('interval', 'day')
    if (!citywide) params.set('bbox', getQuantizedBbox(map))
    if (dataset) params.set('dataset', dataset)
    const query = params.toString()
    if (query === lastCompareQueryRef.current) return
    lastCompareQueryRef.current = query
    if (compareAbortRef.current) compareAbortRef.current.abort()
    const controller = new AbortController()
    compareAbortRef.current = controller
    fetch(`${API_BASE}/v1/compare?${query}`, { signal: controller.signal })
      .then(r => r.json())
      .then((data) => {
        const aTotal = Number(data?.window_a?.totals?.total || 0)
        const bTotal = Number(data?.window_b?.totals?.total || 0)
        const diff = aTotal - bTotal
        const pct = bTotal ? (diff / bTotal) * 100 : null
        setDelta({ diff, pct })
      })
      .catch(() => { /* optional */ })
  }

  const onMoveEnd = (map: L.Map) => {
    fetchIncidents()
  }

  const MapEvents: React.FC<{ onReady: (map: L.Map) => void; onMoveEnd: (map: L.Map) => void }> = ({ onReady, onMoveEnd }) => {
    const map = useMapEvents({
      moveend() {
        // Debounce moveend-triggered fetches
        if (fetchTimerRef.current) window.clearTimeout(fetchTimerRef.current)
        fetchTimerRef.current = window.setTimeout(() => {
          onMoveEnd(map)
          fetchNeighbourhoods()
          fetchAnalytics()
          fetchCompare()
        }, 250)
      },
    })
    React.useEffect(() => {
      onReady(map)
      fetchNeighbourhoods()
      fetchAnalytics()
      fetchCompare()
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])
    return null
  }

  // Fetch stats for min/max report_date
  const fetchStats = React.useCallback(() => {
    setStatsLoading(true)
    fetch(`${API_BASE}/v1/stats`)
      .then(r => r.json())
      .then((data) => {
        const max = data?.max_report_date as string | undefined
        const min = data?.min_report_date as string | undefined
        const etl = data?.last_etl_run_at as string | undefined
        if (max) setStatsMaxDate(max.slice(0, 10))
        if (min) setStatsMinDate(min.slice(0, 10))
        if (etl) setLastEtlRunAt(etl)
      })
      .catch(() => {})
      .finally(() => setStatsLoading(false))
  }, [])

  React.useEffect(() => {
    fetchStats()
  }, [fetchStats])

  // URL state persistence (hash-based)
  React.useEffect(() => {
    // On mount, read state from URL hash if present
    const hash = window.location.hash.replace(/^#/, '')
    if (hash) {
      const usp = new URLSearchParams(hash)
      const ds = usp.get('dataset') || ''
      const df = usp.get('dateFrom') || ''
      const dt = usp.get('dateTo') || ''
      const cw = usp.get('citywide') === '1'
      const cat = usp.get('category')
      const ha = usp.get('hoodA') || ''
      const hb = usp.get('hoodB') || ''
      const iv = (usp.get('interval') as any) || 'day'
      if (ds) setDataset(ds)
      if (df) setDateFrom(df)
      if (dt) setDateTo(dt)
      setCitywide(cw)
      if (cat) setSelectedCategory(cat)
      if (ha) setHoodA(ha)
      if (hb) setHoodB(hb)
      if (iv === 'day' || iv === 'week' || iv === 'month') setInterval(iv)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  React.useEffect(() => {
    // Write current state to URL hash
    const usp = new URLSearchParams()
    if (dataset) usp.set('dataset', dataset)
    if (dateFrom) usp.set('dateFrom', dateFrom)
    if (dateTo) usp.set('dateTo', dateTo)
    if (citywide) usp.set('citywide', '1')
    if (selectedCategory) usp.set('category', selectedCategory)
    if (hoodA) usp.set('hoodA', hoodA)
    if (hoodB) usp.set('hoodB', hoodB)
    if (interval && interval !== 'day') usp.set('interval', interval)
    const s = usp.toString()
    const newHash = s ? '#' + s : ''
    if (window.location.hash !== newHash) {
      window.history.replaceState(null, '', newHash)
    }
  }, [dataset, dateFrom, dateTo, citywide, selectedCategory, hoodA, hoodB, interval])

  const useLatestMonth = () => {
    const apply = (maxStr: string) => {
      const d = new Date(maxStr + 'T00:00:00Z')
      const from = new Date(d)
      from.setUTCDate(from.getUTCDate() - 30)
      const fromIso = from.toISOString().slice(0, 10)
      setDateFrom(fromIso)
      setDateTo(maxStr)
      fetchIncidents(); fetchAnalytics(); fetchCompare()
    }
    if (statsMaxDate) {
      apply(statsMaxDate)
    } else {
      // try fetching stats on-demand
      setStatsLoading(true)
      fetch(`${API_BASE}/v1/stats`)
        .then(r => r.json())
        .then((data) => {
          const max = (data?.max_report_date as string | undefined)?.slice(0, 10)
          if (max) {
            setStatsMaxDate(max)
            const min = data?.min_report_date as string | undefined
            if (min) setStatsMinDate(min.slice(0, 10))
            const etl = data?.last_etl_run_at as string | undefined
            if (etl) setLastEtlRunAt(etl)
            apply(max)
          } else {
            // fallback to today or current dateTo
            const fallback = dateTo || todayIso
            apply(fallback)
          }
        })
        .catch(() => {
          const fallback = dateTo || todayIso
          apply(fallback)
        })
        .finally(() => setStatsLoading(false))
    }
  }

  const useLastNDays = (n: number) => {
    const end = (statsMaxDate || todayIso)
    const endDate = new Date((statsMaxDate || todayIso) + 'T00:00:00Z')
    const start = new Date(endDate)
    start.setUTCDate(start.getUTCDate() - n)
    setDateFrom(start.toISOString().slice(0, 10))
    setDateTo(end)
    fetchIncidents(); fetchAnalytics(); fetchCompare()
  }

  return (
    <div className="h-full">
      {/* Drawer toggle (icon-only) */}
      <IconButton
        onClick={() => setDrawerOpen(!drawerOpen)}
        aria-label="Toggle panel"
        title={drawerOpen ? 'Close panel' : 'Open panel'}
        style={{ left: drawerOpen ? '386px' : '16px' }}
      >
        {drawerOpen ? (
          <svg className="w-5 h-5 text-slate-900" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M15 18l-6-6 6-6" />
          </svg>
        ) : (
          <svg className="w-5 h-5 text-slate-900" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        )}
      </IconButton>

      {/* Side drawer (Tailwind) */}
      <Drawer open={drawerOpen} width={380}>
        <div className="flex flex-col gap-4 max-h-full overflow-y-auto">
          <div className="flex flex-col gap-1">
            <div className="text-lg font-bold tracking-tight">SafetyView</div>
            <div className="text-sm text-slate-600">
              {loading ? 'Loading incidents…' : `${features.length} incidents in view`}
              {error ? ` · Error: ${error}` : ''}
            </div>
          </div>

          {/* Filters section */}
          <div className="flex flex-col gap-3 bg-slate-50 p-3 rounded-lg border border-slate-200">
            <div className="text-xs uppercase tracking-wide text-slate-500">Filters</div>
            <select className="appearance-none border border-slate-200 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200" value={dataset} onChange={(e) => { setDataset(e.target.value); fetchIncidents(); fetchAnalytics(); fetchCompare() }}>
              <option value="">All datasets</option>
              <option value="robbery">robbery</option>
              <option value="theft_over">theft_over</option>
              <option value="break_and_enter">break_and_enter</option>
            </select>
            <div className="flex gap-2">
              <input className="border border-slate-200 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200" type="date" value={dateFrom} onChange={(e) => { setDateFrom(e.target.value); fetchIncidents(); fetchAnalytics(); fetchCompare() }} />
              <input className="border border-slate-200 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200" type="date" value={dateTo} onChange={(e) => { setDateTo(e.target.value); fetchIncidents(); fetchAnalytics(); fetchCompare() }} />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-xs text-slate-600">Interval</label>
              <select className="appearance-none border border-slate-200 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200" value={interval} onChange={(e) => { setInterval(e.target.value as any); fetchAnalytics(); fetchCompare() }}>
                <option value="day">day</option>
                <option value="week">week</option>
                <option value="month">month</option>
              </select>
            </div>
            <div className="flex gap-2 flex-wrap">
              <button className="px-2 py-1 text-sm rounded-md border border-slate-200 bg-white hover:shadow" onClick={() => useLastNDays(7)}>Last 7d</button>
              <button className="px-2 py-1 text-sm rounded-md border border-slate-200 bg-white hover:shadow" onClick={() => useLastNDays(30)}>Last 30d</button>
              <button className="px-2 py-1 text-sm rounded-md border border-slate-200 bg-white hover:shadow disabled:opacity-50" onClick={useLatestMonth} aria-disabled={statsLoading}>
                {statsLoading ? 'Loading…' : 'Use latest month'}
              </button>
            </div>
            <label className="inline-flex items-center gap-2 text-sm">
              <input type="checkbox" checked={citywide} onChange={(e) => { setCitywide(e.target.checked); fetchIncidents(); fetchAnalytics(); fetchCompare() }} />
              City-wide
            </label>
            <div className="text-xs text-slate-600">
              {statsMinDate && statsMaxDate ? (
                <div>Available: {statsMinDate} → {statsMaxDate}</div>
              ) : null}
              {lastEtlRunAt ? (
                <div>Last ETL: {new Date(lastEtlRunAt).toLocaleString()}</div>
              ) : null}
            </div>
          </div>

          {/* Analytics (moved below filters) */}
          {analytics && (
            <div className="flex flex-col gap-3 bg-slate-50 p-3 rounded-lg border border-slate-200">
              <div className="text-xs uppercase tracking-wide text-slate-500">Analytics</div>
              <div className="flex items-center gap-2 flex-wrap">
                <Tooltip text="Total incidents in current filters and dates">
                  <Badge className="text-sm"><strong>{analytics.total}</strong> total</Badge>
                </Tooltip>
                {delta && (
                  <Tooltip text="Change vs previous window">
                    <Badge className={`text-sm ${delta.diff > 0 ? 'text-emerald-600' : (delta.diff < 0 ? 'text-rose-600' : 'text-slate-700')}`}>
                      {delta.diff > 0 ? '+' : ''}{delta.diff} {delta.pct !== null ? `(${delta.pct.toFixed(1)}%)` : ''}
                    </Badge>
                  </Tooltip>
                )}
                {analytics.timeline && analytics.timeline.length > 0 && (
                  <Tooltip text={interval === 'day' ? 'Daily counts' : (interval === 'week' ? 'Weekly counts' : 'Monthly counts')}>
                    <Badge className="text-sm">
                      {interval === 'day' ? (
                        <Sparkline data={analytics.timeline.map(p => p.count)} />
                      ) : (
                        <MiniBars data={analytics.timeline.map((p: any) => ({ label: new Date(p.date).toISOString().slice(0,10), count: p.count }))} />
                      )}
                    </Badge>
                  </Tooltip>
                )}
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                {Object.entries(analytics.by_category)
                  .sort((a, b) => b[1] - a[1])
                  .map(([label, count]) => {
                    const mock = { properties: { mci_category: label } } as any
                    const color = colorFor(mock)
                    const active = selectedCategory && selectedCategory.toLowerCase() === String(label).toLowerCase()
                    return (
                      <button
                        key={label}
                        title={`Filter by ${String(label)}`}
                        onClick={() => {
                          const next = active ? null : String(label)
                          setSelectedCategory(next)
                          fetchIncidents(); fetchAnalytics(); fetchCompare()
                        }}
                        className={`inline-flex items-center gap-2 text-xs px-2 py-1 rounded-full border ${active ? 'border-slate-800' : 'border-slate-200'} bg-white hover:shadow`}
                      >
                        <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: color }} />{label} ({count})
                      </button>
                    )
                  })}
              </div>
            </div>
          )}

          {/* Neighbourhood comparison */}
          <div className="flex flex-col gap-3 bg-slate-50 p-3 rounded-lg border border-slate-200">
            <div className="text-xs uppercase tracking-wide text-slate-500">Neighbourhood comparison</div>
            <div className="text-xs text-slate-600">Compare totals for two neighbourhoods within the same filters and date window.</div>
            <div className="space-y-2">
              <SearchableSelect
                options={neigh && Array.isArray((neigh as any).features) ? (neigh as any).features.map((f: any) => ({
                  value: f.properties.area_long_code,
                  label: f.properties.area_name
                })) : []}
                value={hoodA}
                onChange={setHoodA}
                placeholder="Select neighbourhood A..."
                className="w-full"
              />
              <SearchableSelect
                options={neigh && Array.isArray((neigh as any).features) ? (neigh as any).features.map((f: any) => ({
                  value: f.properties.area_long_code,
                  label: f.properties.area_name
                })) : []}
                value={hoodB}
                onChange={setHoodB}
                placeholder="Select neighbourhood B..."
                className="w-full"
              />
            </div>
            <div>
              <button className="px-2 py-1 text-sm rounded-md border border-slate-200 bg-white hover:shadow disabled:opacity-50" disabled={!hoodA || !hoodB} onClick={async () => {
                const featureByCode = (code: string) => {
                  if (!neigh) return null
                  const list = (neigh as any).features as any[]
                  return list.find(f => f.properties.area_long_code === code)
                }
                const bboxFromGeom = (geom: any): string | null => {
                  if (!geom) return null
                  // Compute bbox from coordinates
                  const recur = (coords: any, acc: number[] | null = null): number[] => {
                    let a = acc || [Infinity, Infinity, -Infinity, -Infinity]
                    if (typeof coords[0] === 'number') {
                      const [lng, lat] = coords
                      a[0] = Math.min(a[0], lng)
                      a[1] = Math.min(a[1], lat)
                      a[2] = Math.max(a[2], lng)
                      a[3] = Math.max(a[3], lat)
                      return a
                    }
                    for (const c of coords) a = recur(c, a)
                    return a
                  }
                  const b = recur(geom.coordinates)
                  return `${b[0]},${b[1]},${b[2]},${b[3]}`
                }
                const fA = featureByCode(hoodA)
                const fB = featureByCode(hoodB)
                if (!fA || !fB) return
                const bboxA = bboxFromGeom(fA.geometry)
                const bboxB = bboxFromGeom(fB.geometry)
                const q = new URLSearchParams()
                q.set('date_from', `${dateFrom}T00:00:00Z`)
                q.set('date_to', (() => { const d = new Date(dateTo + 'T00:00:00Z'); d.setUTCDate(d.getUTCDate() + 1); return d.toISOString().slice(0,19)+'Z' })())
                q.set('interval', 'day')
                if (dataset) q.set('dataset', dataset)
                if (selectedCategory) q.set('mci_category', selectedCategory as string)
                const fetchOne = async (bbox: string | null) => {
                  const params = new URLSearchParams(q)
                  if (bbox) params.set('bbox', bbox)
                  const res = await fetch(`${API_BASE}/v1/analytics?${params.toString()}`)
                  const data = await res.json()
                  return { total: Number(data?.totals?.total || 0), timeline: (data?.timeline || []).map((p: any) => ({ label: new Date(p.date).toISOString().slice(0,10), count: p.count })) }
                }
                const [aRes, bRes] = await Promise.all([
                  fetchOne(bboxA),
                  fetchOne(bboxB),
                ])
                const diff = aRes.total - bRes.total
                const pct = bRes.total ? (diff / bRes.total) * 100 : null
                setHoodCompare({ a: { name: fA.properties.area_name, total: aRes.total }, b: { name: fB.properties.area_name, total: bRes.total }, diff, pct })
                // Render mini bars below with both timelines
                ;(document.getElementById('hood-compare-bars-a') as any)?.replaceChildren()
                ;(document.getElementById('hood-compare-bars-b') as any)?.replaceChildren()
                // Note: We won't manipulate DOM directly further; just keep state for potential future componentization
              }}>Compare</button>
            </div>
            {hoodCompare && (
              <div className="text-sm space-y-3">
                <div className="space-y-3">
                  <div className="p-3 rounded-lg border border-slate-200 bg-white shadow-sm">
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-xs font-medium text-slate-500">A: {hoodCompare.a.name}</div>
                      <div className="text-lg font-bold text-slate-900">{hoodCompare.a.total}</div>
                    </div>
                    <MiniBars className="" data={(analytics?.timeline || []).map((p: any) => ({ label: new Date(p.date).toISOString().slice(0,10), count: p.count }))} />
                  </div>
                  <div className="p-3 rounded-lg border border-slate-200 bg-white shadow-sm">
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-xs font-medium text-slate-500">B: {hoodCompare.b.name}</div>
                      <div className="text-lg font-bold text-slate-900">{hoodCompare.b.total}</div>
                    </div>
                    <MiniBars className="" data={(analytics?.timeline || []).map((p: any) => ({ label: new Date(p.date).toISOString().slice(0,10), count: p.count }))} />
                  </div>
                </div>
                <div className={`text-center text-sm font-medium px-3 py-2 rounded-md ${
                  hoodCompare.diff > 0 ? 'bg-emerald-50 text-emerald-700' : 
                  hoodCompare.diff < 0 ? 'bg-rose-50 text-rose-700' : 
                  'bg-slate-50 text-slate-700'
                }`}>
                  Δ {hoodCompare.diff > 0 ? '+' : ''}{hoodCompare.diff}{hoodCompare.pct !== null ? ` (${hoodCompare.pct.toFixed(1)}%)` : ''}
                </div>
              </div>
            )}
          </div>

          
        </div>
      </Drawer>
      <MapContainer
        className="h-full"
        center={[43.6532, -79.3832]}
        zoom={11}
        zoomControl={false}
        whenReady={() => { /* handled by MapEvents */ }}
      >
        <MapEvents
          onReady={(m) => { mapRef.current = m; fetchIncidents() }}
          onMoveEnd={() => fetchIncidents()}
        />
        <ZoomControl position="bottomright" />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {neigh && (
          <GeoJSON data={neigh as any} style={{ color: '#1d4ed8', weight: 3, opacity: 0.9, fillOpacity: 0.04 }} />
        )}
        {features.length === 0 && (
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-lg text-slate-500 bg-white/85 px-3 py-2 rounded-md border border-[rgba(0,0,0,0.08)]">
            No incidents in the current view
          </div>
        )}
        {features.map((f, idx) => {
          if (f.geometry?.type === 'Point') {
            const [lng, lat] = f.geometry.coordinates
            return (
              <Marker key={idx} position={[lat, lng]} icon={iconFor(f)}>
                <Popup>
                  <div>
                    <div><strong>ID:</strong> {f.properties.id}</div>
                    <div><strong>Dataset:</strong> {f.properties.dataset}</div>
                    <div><strong>Date:</strong> {f.properties.report_datetime || f.properties.report_date}</div>
                    {f.properties.offence ? (<div><strong>Offence:</strong> {f.properties.offence}</div>) : null}
                  </div>
                </Popup>
              </Marker>
            )
          }
          return null
        })}
      </MapContainer>
    </div>
  )
}

createRoot(document.getElementById('root')!).render(<App />)
