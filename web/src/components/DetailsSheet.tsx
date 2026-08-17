import React from 'react'
import { SearchableSelect } from './SearchableSelect'
import { Chip } from './Chip'
import { TrendChart } from './TrendChart'
import { categorySeriesColor, CHART_CURRENT, CHART_PRIOR } from '../lib/colors'
import { alignSeries, niceMax, overlayCaption, orderedCategoryKeys, seriesForCategory } from '../lib/chart'
import { categoryLabel, formatBucketTick, intervalAxisLabel, intervalLabel, overlayTitle } from '../lib/labels'
import type {
  AnalyticsResponse,
  CompareResponse,
  Delta,
  HoodCompare,
  Interval,
  NeighbourhoodFeature,
  OverlayMode,
} from '../lib/types'

type DetailsSheetProps = {
  open: boolean
  onClose: () => void
  title: string
  subtitle?: string
  analytics: AnalyticsResponse | null
  windowCompare: CompareResponse | null
  delta: Delta | null
  interval: Interval
  onInterval: (v: Interval) => void
  neighbourhoods: NeighbourhoodFeature[]
  hoodA: string
  hoodB: string
  onHoodA: (v: string) => void
  onHoodB: (v: string) => void
  onCompare: () => void
  hoodCompare: HoodCompare | null
  error: string | null
  onRetry: () => void
}

function deltaClass(diff: number): string {
  if (diff > 0) return 'text-sv-warn bg-sv-warn-soft'
  if (diff < 0) return 'text-sv-better bg-sv-better-soft'
  return 'text-sv-ink bg-sv-paper-2'
}

function ChartLegend({ items }: { items: Array<{ name: string; color: string }> }) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      {items.map((item) => (
        <span key={item.name} className="inline-flex items-center gap-1.5 text-xs text-sv-muted">
          <span className="h-0.5 w-3.5 rounded-full" style={{ background: item.color }} aria-hidden />
          {item.name}
        </span>
      ))}
    </div>
  )
}

export const DetailsSheet: React.FC<DetailsSheetProps> = ({
  open,
  onClose,
  title,
  subtitle,
  analytics,
  windowCompare,
  delta,
  interval,
  onInterval,
  neighbourhoods,
  hoodA,
  hoodB,
  onHoodA,
  onHoodB,
  onCompare,
  hoodCompare,
  error,
  onRetry,
}) => {
  const [breakdown, setBreakdown] = React.useState(false)
  const options = neighbourhoods.map((f) => ({
    value: f.properties.area_long_code,
    label: f.properties.area_name,
  }))

  const overlayMode: OverlayMode = hoodCompare ? 'hood' : 'window'
  const xLabel = intervalAxisLabel(interval)

  const overlay = React.useMemo(() => {
    if (hoodCompare) {
      let aligned = alignSeries(hoodCompare.a.timeline, hoodCompare.b.timeline)
      if (aligned.labels.length === 0) {
        const fallback = windowCompare?.window_a.timeline || analytics?.timeline || []
        aligned = {
          labels: fallback.map((point) => point.date),
          current: fallback.map(() => 0),
          prior: fallback.map(() => 0),
        }
      }
      return {
        title: `${hoodCompare.a.name} vs ${hoodCompare.b.name}`,
        labels: aligned.labels.map((d) => formatBucketTick(d, interval)),
        series: [
          { name: hoodCompare.a.name, values: aligned.current, color: CHART_CURRENT },
          { name: hoodCompare.b.name, values: aligned.prior, color: CHART_PRIOR },
        ],
      }
    }
    const current = windowCompare?.window_a.timeline || analytics?.timeline || []
    const prior = windowCompare?.window_b.timeline || []
    const aligned = alignSeries(current, prior)
    return {
      title: overlayTitle(overlayMode),
      labels: aligned.labels.map((d) => formatBucketTick(d, interval)),
      series: [
        { name: 'Current window', values: aligned.current, color: CHART_CURRENT },
        { name: 'Previous window', values: aligned.prior, color: CHART_PRIOR },
      ],
    }
  }, [analytics, hoodCompare, interval, overlayMode, windowCompare])

  const categoryPanels = React.useMemo(() => {
    if (hoodCompare) {
      const keys = orderedCategoryKeys([hoodCompare.a.timeline_by_category, hoodCompare.b.timeline_by_category])
      return keys.map((key) => {
        const aligned = alignSeries(
          seriesForCategory(hoodCompare.a.timeline_by_category, key),
          seriesForCategory(hoodCompare.b.timeline_by_category, key),
        )
        return {
          key,
          title: categoryLabel(key),
          labels: aligned.labels.map((d) => formatBucketTick(d, interval)),
          series: [
            { name: hoodCompare.a.name, values: aligned.current, color: CHART_CURRENT },
            { name: hoodCompare.b.name, values: aligned.prior, color: CHART_PRIOR },
          ],
        }
      })
    }
    const currentByCat = windowCompare?.window_a.timeline_by_category || analytics?.timeline_by_category || {}
    const priorByCat = windowCompare?.window_b.timeline_by_category || {}
    const keys = orderedCategoryKeys([currentByCat, priorByCat])
    return keys.map((key) => {
      const current = seriesForCategory(currentByCat, key)
      const prior = seriesForCategory(priorByCat, key)
      const aligned = alignSeries(current, prior)
      const series =
        prior.length > 0
          ? [
              { name: 'Current window', values: aligned.current, color: CHART_CURRENT },
              { name: 'Previous window', values: aligned.prior, color: CHART_PRIOR },
            ]
          : [{ name: categoryLabel(key), values: aligned.current, color: categorySeriesColor(key) }]
      return {
        key,
        title: categoryLabel(key),
        labels: aligned.labels.map((d) => formatBucketTick(d, interval)),
        series,
      }
    })
  }, [analytics, hoodCompare, interval, windowCompare])

  const sharedYMax = Math.max(0, ...categoryPanels.flatMap((panel) => panel.series.flatMap((s) => s.values)))
  const canBreakdown = categoryPanels.length > 0

  return (
    <aside
      className={[
        'fixed z-[1100] flex flex-col bg-sv-paper text-sv-ink shadow-paper',
        'border-sv-ink/10',
        'max-md:inset-x-0 max-md:bottom-0 max-md:max-h-[64vh] max-md:rounded-t-xl max-md:border-t',
        'md:inset-y-0 md:right-0 md:w-[460px] md:border-l',
        'transition-[transform,opacity] duration-200 ease-out',
        open ? 'translate-y-0 opacity-100 md:translate-x-0' : 'pointer-events-none opacity-0 max-md:translate-y-full md:translate-x-full',
      ].join(' ')}
      aria-hidden={!open}
    >
      <div className="flex items-start justify-between gap-3 border-b border-sv-ink/10 px-5 py-4">
        <div className="min-w-0">
          <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-sv-accent">Details</div>
          <h2 className="font-display truncate text-xl font-bold tracking-tight text-sv-ink">{title}</h2>
          {subtitle ? <p className="mt-0.5 text-sm text-sv-muted">{subtitle}</p> : null}
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close details"
          className="grid h-11 w-11 shrink-0 place-items-center rounded-md border border-sv-ink/10 text-sv-ink transition-transform duration-150 ease-out hover:bg-sv-ink/[0.04] active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sv-accent"
        >
          <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M6 6l12 12M18 6L6 18" />
          </svg>
        </button>
      </div>
      <div className="flex-1 space-y-5 overflow-y-auto px-5 py-5">
        {error ? (
          <div className="rounded-md border border-sv-warn/20 bg-sv-warn-soft px-3 py-3 text-sm text-sv-warn">
            <div>{error}</div>
            <button
              type="button"
              onClick={onRetry}
              className="mt-2 h-11 rounded-md bg-sv-accent px-3 text-sm font-semibold text-sv-on-accent transition-transform duration-150 ease-out hover:bg-sv-accent-strong active:scale-[0.98]"
            >
              Retry
            </button>
          </div>
        ) : null}

        {analytics ? (
          <section>
            <div className="text-[11px] font-medium uppercase tracking-[0.14em] text-sv-muted">Period</div>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <div className="font-mono text-3xl font-medium tabular-nums tracking-tight">{analytics.totals.total.toLocaleString()}</div>
              {delta ? (
                <span className={`rounded-md px-2 py-1 text-sm font-medium ${deltaClass(delta.diff)}`}>
                  {delta.diff > 0 ? '+' : ''}
                  {delta.diff}
                  {delta.pct !== null ? ` (${delta.pct.toFixed(1)}%)` : ''} vs prior
                </span>
              ) : null}
            </div>
            <p className="mt-1 text-xs text-sv-muted">More incidents than the previous window is flagged as a warning.</p>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              {(['day', 'week', 'month'] as const).map((iv) => (
                <Chip key={iv} active={interval === iv} onClick={() => onInterval(iv)}>
                  {intervalLabel(iv)}
                </Chip>
              ))}
              <Chip
                active={breakdown}
                disabled={!canBreakdown}
                title={canBreakdown ? 'Show one chart per MCI category' : 'Category timeline unavailable'}
                onClick={() => setBreakdown((v) => !v)}
              >
                By category
              </Chip>
            </div>

            <div className="mt-4 rounded-md border border-sv-ink/10 bg-white/70 p-3">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="text-sm font-semibold text-sv-ink">{overlay.title}</div>
                <ChartLegend items={overlay.series.map((s) => ({ name: s.name, color: s.color }))} />
              </div>
              <div className="mt-2 min-h-[200px]">
                <TrendChart
                  categories={overlay.labels}
                  series={overlay.series}
                  height={220}
                  ariaLabel={overlay.title}
                />
              </div>
              <p className="mt-1 text-[11px] leading-snug text-sv-muted">{overlayCaption(overlayMode, interval, xLabel)}</p>
            </div>

            {breakdown && canBreakdown ? (
              <div className="mt-3 space-y-3">
                <div className="text-[11px] font-medium uppercase tracking-[0.14em] text-sv-muted">By category</div>
                {categoryPanels.map((panel) => (
                  <div key={panel.key} className="rounded-md border border-sv-ink/10 bg-white/70 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div className="text-sm font-semibold text-sv-ink">{panel.title}</div>
                      <ChartLegend items={panel.series.map((s) => ({ name: s.name, color: s.color }))} />
                    </div>
                    <TrendChart
                      categories={panel.labels}
                      series={panel.series}
                      height={140}
                      yMax={sharedYMax}
                      compact
                      ariaLabel={`${panel.title} reported incidents`}
                    />
                  </div>
                ))}
                <p className="text-[11px] leading-snug text-sv-muted">
                  Shared scale 0 to {niceMax(Math.max(sharedYMax, 1))} so mix stays honest. Robbery is not stretched to match
                  break and enter.
                </p>
              </div>
            ) : null}

            <div className="mt-3 flex flex-wrap gap-1.5">
              {Object.entries(analytics.totals.by_category)
                .sort((a, b) => b[1] - a[1])
                .map(([label, count]) => (
                  <span key={label} className="rounded-full border border-sv-ink/10 bg-white/70 px-2.5 py-1 text-xs">
                    {categoryLabel(label)} · <span className="font-mono tabular-nums">{count}</span>
                  </span>
                ))}
            </div>
          </section>
        ) : null}

        <section>
          <div className="text-[11px] font-medium uppercase tracking-[0.14em] text-sv-muted">Compare neighbourhoods</div>
          <p className="mt-1 text-xs text-sv-muted">
            One overlay, two neighbourhoods, same dates. The large chart switches to this pair after you compare.
          </p>
          <div className="mt-2 space-y-2">
            <SearchableSelect options={options} value={hoodA} onChange={onHoodA} placeholder="Neighbourhood A" />
            <SearchableSelect options={options} value={hoodB} onChange={onHoodB} placeholder="Neighbourhood B" />
          </div>
          <button
            type="button"
            disabled={!hoodA || !hoodB}
            onClick={onCompare}
            className="mt-2 h-11 w-full rounded-md bg-sv-accent text-sm font-semibold text-sv-on-accent transition-transform duration-150 ease-out hover:bg-sv-accent-strong active:scale-[0.98] disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sv-accent focus-visible:ring-offset-2 focus-visible:ring-offset-sv-paper"
          >
            Compare
          </button>
          {hoodCompare ? (
            <div className="mt-3 space-y-2">
              <div className="grid grid-cols-2 gap-2">
                <div className="rounded-md border border-sv-ink/10 bg-white/70 p-3">
                  <div className="text-xs text-sv-muted">{hoodCompare.a.name}</div>
                  <div className="font-mono text-lg font-medium tabular-nums">{hoodCompare.a.total}</div>
                </div>
                <div className="rounded-md border border-sv-ink/10 bg-white/70 p-3">
                  <div className="text-xs text-sv-muted">{hoodCompare.b.name}</div>
                  <div className="font-mono text-lg font-medium tabular-nums">{hoodCompare.b.total}</div>
                </div>
              </div>
              <div className={`rounded-md px-3 py-2 text-center text-sm font-medium ${deltaClass(hoodCompare.diff)}`}>
                {hoodCompare.diff > 0 ? '+' : ''}
                {hoodCompare.diff}
                {hoodCompare.pct !== null ? ` (${hoodCompare.pct.toFixed(1)}%)` : ''} · A vs B
              </div>
            </div>
          ) : null}
        </section>
      </div>
    </aside>
  )
}
