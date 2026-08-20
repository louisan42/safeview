import React from 'react'
import L from 'leaflet'
import { TopBar } from './components/TopBar'
import { DetailsSheet } from './components/DetailsSheet'
import { MapCanvas } from './components/MapCanvas'
import { EmptyState } from './components/EmptyState'
import { ChoroplethLegend } from './components/ChoroplethLegend'
import { choroplethUrl, compareUrl, incidentsUrl, metaUrl, neighbourhoodsUrl, statsUrl, analyticsUrl } from './lib/api'
import { deployHoverTitle, displaySha, formatTpsThroughLine, formatUpdatedLine, publishedLagNote } from './lib/buildStamp'
import { fetchJson, humanizeError, isAbortError } from './lib/http'
import { clampDate, endOfDayZ, lastNDaysOfData, nextDayStartZ, startOfDayZ, windowOverlapsData } from './lib/dates'
import { categoryLabel, timePresetDays } from './lib/labels'
import { colorForIncident } from './lib/colors'
import type {
  AnalyticsResponse,
  CompareResponse,
  DatasetKey,
  Delta,
  GeocodeHit,
  HoodCompare,
  IncidentCollection,
  IncidentFeature,
  Interval,
  MetaResponse,
  NeighbourhoodCollection,
  NeighbourhoodFeature,
  NeighbourhoodMatch,
  Scope,
  StatsResponse,
  TimePreset,
} from './lib/types'

/** Match GET /v1/incidents max (`le=5000`). Bbox-scoped fetches stay well under a full-city dump; clustering keeps the DOM small. */
const INCIDENT_LIMIT = 5000

function quantizedBbox(map: L.Map): string {
  const b = map.getBounds()
  const q = (n: number) => Number(n.toFixed(4))
  return `${q(b.getWest())},${q(b.getSouth())},${q(b.getEast())},${q(b.getNorth())}`
}

export function App() {
  const [features, setFeatures] = React.useState<IncidentFeature[]>([])
  const [total, setTotal] = React.useState(0)
  const [choropleth, setChoropleth] = React.useState<NeighbourhoodCollection | null>(null)
  const [hoodList, setHoodList] = React.useState<NeighbourhoodFeature[]>([])
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [dataset, setDataset] = React.useState<'' | DatasetKey>('')
  const [dateFrom, setDateFrom] = React.useState('')
  const [dateTo, setDateTo] = React.useState('')
  const [preset, setPreset] = React.useState<TimePreset>('7d')
  const [scope, setScope] = React.useState<Scope>('map')
  const [rangeReady, setRangeReady] = React.useState(false)
  const [statsMaxDate, setStatsMaxDate] = React.useState<string | null>(null)
  const [statsMinDate, setStatsMinDate] = React.useState<string | null>(null)
  const [lastEtlRunAt, setLastEtlRunAt] = React.useState<string | null>(null)
  const [apiMeta, setApiMeta] = React.useState<MetaResponse | null>(null)
  const [selectedCategory, setSelectedCategory] = React.useState<string | null>(null)
  const [selectedHood, setSelectedHood] = React.useState<NeighbourhoodFeature | null>(null)
  const [sheetOpen, setSheetOpen] = React.useState(false)
  const [mapReady, setMapReady] = React.useState(false)
  const [analytics, setAnalytics] = React.useState<AnalyticsResponse | null>(null)
  const [detailAnalytics, setDetailAnalytics] = React.useState<AnalyticsResponse | null>(null)
  const [windowCompare, setWindowCompare] = React.useState<CompareResponse | null>(null)
  const [delta, setDelta] = React.useState<Delta | null>(null)
  const [interval, setInterval] = React.useState<Interval>('day')
  const [hoodA, setHoodA] = React.useState('')
  const [hoodB, setHoodB] = React.useState('')
  const [hoodCompareOn, setHoodCompareOn] = React.useState(false)
  const [hoodCompare, setHoodCompare] = React.useState<HoodCompare | null>(null)
  const [flyTo, setFlyTo] = React.useState<{ lat: number; lng: number; zoom?: number } | null>(null)

  const mapRef = React.useRef<L.Map | null>(null)
  const fetchTimerRef = React.useRef<number | null>(null)
  const abortIncidents = React.useRef<AbortController | null>(null)
  const abortAnalytics = React.useRef<AbortController | null>(null)
  const abortCompare = React.useRef<AbortController | null>(null)
  const hashSkipRef = React.useRef(true)

  const citywide = scope === 'city'
  const hoodNames = React.useMemo(() => {
    const m = new Map<string, string>()
    for (const f of choropleth?.features || hoodList) {
      m.set(f.properties.area_long_code, f.properties.area_name)
      if (f.properties.area_short_code) m.set(f.properties.area_short_code, f.properties.area_name)
    }
    return m
  }, [choropleth, hoodList])

  const applyLatestWindow = React.useCallback((maxStr: string, minStr: string | null, days = 7) => {
    const w = lastNDaysOfData(maxStr, days, minStr)
    setDateFrom(w.from)
    setDateTo(w.to)
    setPreset(days === 7 ? '7d' : days === 30 ? '30d' : days === 90 ? '90d' : 'custom')
  }, [])

  React.useEffect(() => {
    const hash = window.location.hash.replace(/^#/, '')
    const usp = hash ? new URLSearchParams(hash) : null
    let cancelled = false
    ;(async () => {
      try {
        const [data, meta] = await Promise.all([
          fetchJson<StatsResponse>(statsUrl()),
          fetchJson<MetaResponse>(metaUrl()).catch(() => null),
        ])
        if (cancelled) return
        const max = data.max_report_date ? data.max_report_date.slice(0, 10) : null
        const min = data.min_report_date ? data.min_report_date.slice(0, 10) : null
        setStatsMaxDate(max)
        setStatsMinDate(min)
        setLastEtlRunAt(data.last_etl_run_at)
        if (meta) setApiMeta(meta)
        const ds = (usp?.get('dataset') || '') as '' | DatasetKey
        const df = usp?.get('dateFrom') || ''
        const dt = usp?.get('dateTo') || ''
        const cw = usp?.get('citywide') === '1'
        const cat = usp?.get('category')
        const ha = usp?.get('hoodA') || ''
        const hb = usp?.get('hoodB') || ''
        const iv = usp?.get('interval') as Interval | null
        const pr = usp?.get('preset') as TimePreset | null
        if (ds === 'robbery' || ds === 'theft_over' || ds === 'break_and_enter' || ds === '') setDataset(ds)
        if (cw) setScope('city')
        if (cat) setSelectedCategory(cat)
        if (ha) setHoodA(ha)
        if (hb) setHoodB(hb)
        if (iv === 'day' || iv === 'week' || iv === 'month') setInterval(iv)
        if (pr === '7d' || pr === '30d' || pr === '90d' || pr === 'custom') setPreset(pr)
        if (df && dt && max) {
          setDateFrom(clampDate(df, min, max))
          setDateTo(clampDate(dt, min, max))
          if (!pr) setPreset('custom')
        } else if (max) {
          applyLatestWindow(max, min, 7)
        }
      } catch (err) {
        if (!isAbortError(err)) setError(humanizeError(err))
      } finally {
        if (!cancelled) {
          hashSkipRef.current = false
          setRangeReady(true)
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [applyLatestWindow])

  React.useEffect(() => {
    if (hashSkipRef.current || !rangeReady) return
    const usp = new URLSearchParams()
    if (dataset) usp.set('dataset', dataset)
    if (dateFrom) usp.set('dateFrom', dateFrom)
    if (dateTo) usp.set('dateTo', dateTo)
    if (scope === 'city') usp.set('citywide', '1')
    if (selectedCategory) usp.set('category', selectedCategory)
    if (hoodA) usp.set('hoodA', hoodA)
    if (hoodB) usp.set('hoodB', hoodB)
    if (interval !== 'day') usp.set('interval', interval)
    if (preset !== '7d') usp.set('preset', preset)
    const s = usp.toString()
    const newHash = s ? '#' + s : ''
    if (window.location.hash !== newHash) window.history.replaceState(null, '', newHash || window.location.pathname)
  }, [dataset, dateFrom, dateTo, scope, selectedCategory, hoodA, hoodB, interval, preset, rangeReady])

  const sharedParams = React.useCallback(
    (forAnalytics = false) => {
      const params = new URLSearchParams()
      if (dataset) params.set('dataset', dataset)
      if (selectedCategory) params.set('mci_category', selectedCategory)
      if (dateFrom) params.set('date_from', forAnalytics ? startOfDayZ(dateFrom) : startOfDayZ(dateFrom))
      if (dateTo) params.set('date_to', forAnalytics ? nextDayStartZ(dateTo) : endOfDayZ(dateTo))
      return params
    },
    [dataset, selectedCategory, dateFrom, dateTo],
  )

  const fetchIncidents = React.useCallback(() => {
    const map = mapRef.current
    if (!map || !rangeReady || !dateFrom || !dateTo) return
    const params = sharedParams(false)
    params.set('limit', String(INCIDENT_LIMIT))
    if (!citywide) params.set('bbox', quantizedBbox(map))
    if (abortIncidents.current) abortIncidents.current.abort()
    const controller = new AbortController()
    abortIncidents.current = controller
    setLoading(true)
    fetchJson<IncidentCollection>(incidentsUrl(params), controller.signal)
      .then((fc) => {
        setFeatures(fc.features || [])
        setTotal(typeof fc.total === 'number' ? fc.total : (fc.features || []).length)
        setError(null)
      })
      .catch((err) => {
        if (isAbortError(err)) return
        setError(humanizeError(err))
      })
      .finally(() => setLoading(false))
  }, [citywide, dateFrom, dateTo, rangeReady, sharedParams])

  const fetchChoropleth = React.useCallback(() => {
    if (!rangeReady || !dateFrom || !dateTo) return
    const params = sharedParams(false)
    fetchJson<NeighbourhoodCollection>(choroplethUrl(params))
      .then((fc) => {
        setChoropleth(fc)
        setHoodList(fc.features || [])
      })
      .catch((err) => {
        if (isAbortError(err)) return
      })
  }, [dateFrom, dateTo, rangeReady, sharedParams])

  const fetchHoodNamesFallback = React.useCallback(() => {
    fetchJson<NeighbourhoodCollection>(neighbourhoodsUrl(new URLSearchParams({ limit: '5000' })))
      .then((fc) => {
        if (fc.features?.length) setHoodList(fc.features)
      })
      .catch((err) => {
        if (isAbortError(err)) return
      })
  }, [])

  const fetchAnalytics = React.useCallback(() => {
    const map = mapRef.current
    if (!map || !rangeReady || !dateFrom || !dateTo) return
    const params = sharedParams(true)
    params.set('interval', interval)
    if (!citywide) params.set('bbox', quantizedBbox(map))
    if (abortAnalytics.current) abortAnalytics.current.abort()
    const controller = new AbortController()
    abortAnalytics.current = controller
    fetchJson<AnalyticsResponse>(analyticsUrl(params), controller.signal)
      .then(setAnalytics)
      .catch((err) => {
        if (isAbortError(err)) return
      })
  }, [citywide, dateFrom, dateTo, interval, rangeReady, sharedParams])

  const fetchCompare = React.useCallback(() => {
    const map = mapRef.current
    if (!map || !rangeReady || !dateFrom || !dateTo) return
    const start = new Date(startOfDayZ(dateFrom))
    const end = new Date(nextDayStartZ(dateTo))
    const ms = end.getTime() - start.getTime()
    const prevEnd = new Date(start.getTime())
    const prevStart = new Date(start.getTime() - ms)
    const params = new URLSearchParams()
    params.set('a_date_from', start.toISOString())
    params.set('a_date_to', end.toISOString())
    params.set('b_date_from', prevStart.toISOString())
    params.set('b_date_to', prevEnd.toISOString())
    params.set('interval', interval)
    if (dataset) params.set('dataset', dataset)
    if (selectedCategory) params.set('mci_category', selectedCategory)
    if (selectedHood) params.set('hood', selectedHood.properties.area_long_code)
    else if (!citywide) params.set('bbox', quantizedBbox(map))
    if (abortCompare.current) abortCompare.current.abort()
    const controller = new AbortController()
    abortCompare.current = controller
    fetchJson<CompareResponse>(compareUrl(params), controller.signal)
      .then((data) => {
        const aTotal = Number(data.window_a?.totals?.total || 0)
        const bTotal = Number(data.window_b?.totals?.total || 0)
        const diff = aTotal - bTotal
        const pct = bTotal ? (diff / bTotal) * 100 : null
        setWindowCompare(data)
        setDelta({ diff, pct })
      })
      .catch((err) => {
        if (isAbortError(err)) return
      })
  }, [citywide, dataset, dateFrom, dateTo, interval, rangeReady, selectedCategory, selectedHood])

  const refreshAll = React.useCallback(() => {
    fetchIncidents()
    fetchChoropleth()
    fetchAnalytics()
    fetchCompare()
  }, [fetchAnalytics, fetchChoropleth, fetchCompare, fetchIncidents])

  const onMapReady = React.useCallback(
    (map: L.Map) => {
      mapRef.current = map
      setMapReady(true)
      fetchHoodNamesFallback()
    },
    [fetchHoodNamesFallback],
  )

  const onMoveEnd = React.useCallback(
    (map: L.Map) => {
      mapRef.current = map
      if (fetchTimerRef.current) window.clearTimeout(fetchTimerRef.current)
      fetchTimerRef.current = window.setTimeout(() => {
        fetchIncidents()
        fetchAnalytics()
        fetchCompare()
      }, 250)
    },
    [fetchAnalytics, fetchCompare, fetchIncidents],
  )

  React.useEffect(() => {
    if (!rangeReady || !mapReady) return
    refreshAll()
  }, [rangeReady, mapReady, dataset, selectedCategory, dateFrom, dateTo, scope, interval, selectedHood, refreshAll])

  React.useEffect(() => {
    if (!selectedHood || !rangeReady || !dateFrom || !dateTo) {
      setDetailAnalytics(null)
      return
    }
    const params = sharedParams(true)
    params.set('interval', interval)
    params.set('hood', selectedHood.properties.area_long_code)
    fetchJson<AnalyticsResponse>(analyticsUrl(params))
      .then(setDetailAnalytics)
      .catch((err) => {
        if (isAbortError(err)) return
      })
  }, [dataset, dateFrom, dateTo, interval, rangeReady, selectedCategory, selectedHood, sharedParams])

  React.useEffect(() => {
    if (!hoodCompareOn || !hoodA || !hoodB || !rangeReady || !dateFrom || !dateTo) {
      if (!hoodCompareOn) setHoodCompare(null)
      return
    }
    let cancelled = false
    const params = sharedParams(true)
    params.set('interval', interval)
    const fetchOne = async (code: string) => {
      const p = new URLSearchParams(params)
      p.set('hood', code)
      return fetchJson<AnalyticsResponse>(analyticsUrl(p))
    }
    Promise.all([fetchOne(hoodA), fetchOne(hoodB)])
      .then(([aRes, bRes]) => {
        if (cancelled) return
        const nameOf = (code: string) => hoodNames.get(code) || code
        const diff = aRes.totals.total - bRes.totals.total
        const pct = bRes.totals.total ? (diff / bRes.totals.total) * 100 : null
        setHoodCompare({
          a: {
            code: hoodA,
            name: nameOf(hoodA),
            total: aRes.totals.total,
            timeline: aRes.timeline || [],
            timeline_by_category: aRes.timeline_by_category || {},
          },
          b: {
            code: hoodB,
            name: nameOf(hoodB),
            total: bRes.totals.total,
            timeline: bRes.timeline || [],
            timeline_by_category: bRes.timeline_by_category || {},
          },
          diff,
          pct,
        })
        setSheetOpen(true)
      })
      .catch((err) => {
        if (cancelled || isAbortError(err)) return
        setError(humanizeError(err))
      })
    return () => {
      cancelled = true
    }
  }, [dateFrom, dateTo, hoodA, hoodB, hoodCompareOn, hoodNames, interval, rangeReady, sharedParams])

  const onPreset = (p: TimePreset) => {
    setPreset(p)
    const days = timePresetDays(p)
    if (days && statsMaxDate) applyLatestWindow(statsMaxDate, statsMinDate, days)
  }

  const onDateFrom = (v: string) => {
    setPreset('custom')
    setDateFrom(clampDate(v, statsMinDate, statsMaxDate))
  }
  const onDateTo = (v: string) => {
    setPreset('custom')
    setDateTo(clampDate(v, statsMinDate, statsMaxDate))
  }

  const jumpLatest = () => {
    if (statsMaxDate) applyLatestWindow(statsMaxDate, statsMinDate, 7)
  }

  const onLocate = (hit: GeocodeHit, neighbourhood: NeighbourhoodMatch | null) => {
    setFlyTo({ lat: hit.lat, lng: hit.lng, zoom: 15 })
    setScope('map')
    if (neighbourhood) {
      const feat =
        (choropleth?.features || hoodList).find(
          (f) => f.properties.area_long_code === neighbourhood.area_long_code,
        ) || {
          type: 'Feature' as const,
          geometry: null,
          properties: {
            area_long_code: neighbourhood.area_long_code,
            area_short_code: neighbourhood.area_short_code,
            area_name: neighbourhood.area_name,
          },
        }
      setSelectedHood(feat)
      setSheetOpen(true)
    } else {
      setSheetOpen(true)
    }
  }

  const onSelectHood = (feature: NeighbourhoodFeature) => {
    setSelectedHood(feature)
    setSheetOpen(true)
  }

  const compareHoods = () => {
    if (!hoodA || !hoodB) return
    setHoodCompareOn(true)
    setSheetOpen(true)
  }

  const categoryChips = Object.entries(analytics?.totals.by_category || {})
    .sort((a, b) => b[1] - a[1])
    .map(([label, count]) => ({
      label: categoryLabel(label),
      value: label,
      count,
      color: colorForIncident({ properties: { mci_category: label } }),
    }))

  const maxCount = Math.max(0, ...(choropleth?.features || []).map((f) => Number(f.properties.incident_count || 0)))
  const outside = Boolean(dateFrom && dateTo && !windowOverlapsData(dateFrom, dateTo, statsMinDate, statsMaxDate))
  const showEmpty = rangeReady && !loading && features.length === 0 && !error

  const sheetTitle = selectedHood?.properties.area_name || 'Toronto'
  const sheetSub = selectedHood
    ? `${Number(selectedHood.properties.incident_count || 0).toLocaleString()} incidents in this window`
    : citywide
      ? 'City-wide'
      : 'Current map extent'
  const gitSha = displaySha(apiMeta?.git_sha, import.meta.env.VITE_GIT_SHA)
  const appTitle = deployHoverTitle(apiMeta?.deployment_id, apiMeta?.version)
  const updatedLine = formatUpdatedLine(lastEtlRunAt)
  const tpsLine = formatTpsThroughLine(statsMaxDate)
  const lagNote = publishedLagNote(statsMaxDate)

  return (
    <div className="relative h-full bg-sv-paper">
      <MapCanvas
        choropleth={choropleth}
        incidents={features}
        selectedCode={selectedHood?.properties.area_long_code || null}
        hoodNames={hoodNames}
        onReady={onMapReady}
        onMoveEnd={onMoveEnd}
        onSelectHood={onSelectHood}
        flyTo={flyTo}
      />
      <TopBar
        dataset={dataset}
        onDataset={setDataset}
        preset={preset}
        onPreset={onPreset}
        dateFrom={dateFrom}
        dateTo={dateTo}
        minDate={statsMinDate}
        maxDate={statsMaxDate}
        onDateFrom={onDateFrom}
        onDateTo={onDateTo}
        scope={scope}
        onScope={setScope}
        categoryChips={categoryChips}
        selectedCategory={selectedCategory}
        onCategory={setSelectedCategory}
        onLocate={onLocate}
        showing={{ n: features.length, m: total, loading }}
        gitSha={gitSha}
        appTitle={appTitle}
        updatedLine={updatedLine}
        tpsLine={tpsLine}
        lagNote={lagNote}
      />
      <div className="pointer-events-none absolute bottom-20 left-3 z-[1000] flex flex-col items-start gap-2 md:bottom-6 md:left-14">
        <ChoroplethLegend max={maxCount} />
      </div>
      {showEmpty ? (
        <div className="pointer-events-none absolute inset-0 z-[900] flex items-center justify-center p-4">
          <EmptyState outsideRange={outside} minDate={statsMinDate} maxDate={statsMaxDate} onJump={jumpLatest} />
        </div>
      ) : null}
      {!sheetOpen ? (
        <button
          type="button"
          className="sv-panel absolute bottom-4 right-3 z-[1000] h-11 rounded-md px-4 text-sm font-medium text-sv-ink transition-transform duration-150 ease-out active:scale-[0.98] md:top-auto"
          onClick={() => setSheetOpen(true)}
        >
          Details
        </button>
      ) : null}
      <DetailsSheet
        open={sheetOpen}
        onClose={() => {
          setSheetOpen(false)
          setSelectedHood(null)
        }}
        title={sheetTitle}
        subtitle={sheetSub}
        analytics={detailAnalytics || analytics}
        windowCompare={windowCompare}
        delta={delta}
        interval={interval}
        onInterval={setInterval}
        neighbourhoods={hoodList}
        hoodA={hoodA}
        hoodB={hoodB}
        onHoodA={setHoodA}
        onHoodB={setHoodB}
        onCompare={compareHoods}
        hoodCompare={hoodCompare}
        error={error}
        onRetry={refreshAll}
        gitSha={gitSha}
        appTitle={appTitle}
        updatedLine={updatedLine}
        tpsLine={tpsLine}
        lagNote={lagNote}
      />
    </div>
  )
}
