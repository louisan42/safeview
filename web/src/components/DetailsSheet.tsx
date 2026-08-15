import React from 'react'
import { SearchableSelect } from './SearchableSelect'
import { MiniBars } from './MiniBars'
import { Sparkline } from './Sparkline'
import { Chip } from './Chip'
import { ACCENT } from '../lib/colors'
import type { AnalyticsResponse, Delta, HoodCompare, Interval, NeighbourhoodFeature } from '../lib/types'
import { categoryLabel } from '../lib/labels'

type DetailsSheetProps = {
  open: boolean
  onClose: () => void
  title: string
  subtitle?: string
  analytics: AnalyticsResponse | null
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

export const DetailsSheet: React.FC<DetailsSheetProps> = ({
  open,
  onClose,
  title,
  subtitle,
  analytics,
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
  const options = neighbourhoods.map((f) => ({
    value: f.properties.area_long_code,
    label: f.properties.area_name,
  }))

  return (
    <aside
      className={[
        'fixed z-[1100] flex flex-col bg-sv-paper text-sv-ink shadow-paper',
        'border-sv-ink/10',
        'max-md:inset-x-0 max-md:bottom-0 max-md:max-h-[52vh] max-md:rounded-t-xl max-md:border-t',
        'md:inset-y-0 md:right-0 md:w-[380px] md:border-l',
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
            <div className="mt-3 flex items-center gap-2">
              {(['day', 'week', 'month'] as const).map((iv) => (
                <Chip key={iv} active={interval === iv} onClick={() => onInterval(iv)} className="capitalize">
                  {iv}
                </Chip>
              ))}
            </div>
            {analytics.timeline.length > 0 ? (
              <div className="mt-3 rounded-md border border-sv-ink/10 bg-white/60 px-3 py-2">
                {interval === 'day' ? (
                  <Sparkline data={analytics.timeline.map((p) => p.count)} stroke={ACCENT} width={280} height={36} />
                ) : (
                  <MiniBars
                    data={analytics.timeline.map((p) => ({ label: String(p.date).slice(0, 10), count: p.count }))}
                    barColor={ACCENT}
                    height={36}
                  />
                )}
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
          <p className="mt-1 text-xs text-sv-muted">Each chart uses that neighbourhood’s own timeline, with the same filters as the map.</p>
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
              <div className="rounded-md border border-sv-ink/10 bg-white/70 p-3">
                <div className="flex items-baseline justify-between">
                  <div className="text-xs text-sv-muted">{hoodCompare.a.name}</div>
                  <div className="font-mono text-lg font-medium tabular-nums">{hoodCompare.a.total}</div>
                </div>
                <MiniBars className="mt-2" data={hoodCompare.a.timeline} barColor={ACCENT} />
              </div>
              <div className="rounded-md border border-sv-ink/10 bg-white/70 p-3">
                <div className="flex items-baseline justify-between">
                  <div className="text-xs text-sv-muted">{hoodCompare.b.name}</div>
                  <div className="font-mono text-lg font-medium tabular-nums">{hoodCompare.b.total}</div>
                </div>
                <MiniBars className="mt-2" data={hoodCompare.b.timeline} barColor={ACCENT} />
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
