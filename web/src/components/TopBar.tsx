import React from 'react'
import { DATASET_OPTIONS, timePresetLabel } from '../lib/labels'
import type { DatasetKey, GeocodeHit, NeighbourhoodMatch, Scope, TimePreset } from '../lib/types'
import { AddressSearch } from './AddressSearch'
import { Chip } from './Chip'

const PRESETS: TimePreset[] = ['7d', '30d', '90d']

type TopBarProps = {
  dataset: '' | DatasetKey
  onDataset: (v: '' | DatasetKey) => void
  preset: TimePreset
  onPreset: (p: TimePreset) => void
  dateFrom: string
  dateTo: string
  minDate: string | null
  maxDate: string | null
  onDateFrom: (v: string) => void
  onDateTo: (v: string) => void
  scope: Scope
  onScope: (s: Scope) => void
  categoryChips: Array<{ label: string; value: string; count: number; color: string }>
  selectedCategory: string | null
  onCategory: (value: string | null) => void
  onLocate: (hit: GeocodeHit, neighbourhood: NeighbourhoodMatch | null) => void
  showing: { n: number; m: number; loading: boolean }
}

export const TopBar: React.FC<TopBarProps> = ({
  dataset,
  onDataset,
  preset,
  onPreset,
  dateFrom,
  dateTo,
  minDate,
  maxDate,
  onDateFrom,
  onDateTo,
  scope,
  onScope,
  categoryChips,
  selectedCategory,
  onCategory,
  onLocate,
  showing,
}) => {
  return (
    <header className="pointer-events-none absolute inset-x-0 top-0 z-[1000] p-3 md:p-4">
      <div className="pointer-events-auto mx-auto flex max-w-[1400px] flex-col gap-2">
        <div className="sv-panel relative z-20 flex flex-wrap items-center gap-2 rounded-md px-4 py-2.5">
          <div className="flex min-w-[9rem] items-center gap-2.5 pr-3">
            <img src="/logo.svg" alt="" width={32} height={32} className="h-8 w-8 shrink-0 rounded-lg" aria-hidden="true" />
            <div className="flex flex-col">
              <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-sv-accent">Toronto</div>
              <div className="font-display text-lg font-bold leading-tight tracking-tight text-sv-ink">Lotline</div>
            </div>
          </div>
          <AddressSearch onLocate={onLocate} />
          <div className="flex flex-wrap items-center gap-1">
            {PRESETS.map((p) => (
              <Chip key={p} active={preset === p} onClick={() => onPreset(p)}>
                {timePresetLabel(p)}
              </Chip>
            ))}
            <Chip active={preset === 'custom'} onClick={() => onPreset('custom')}>
              Custom
            </Chip>
          </div>
          {preset === 'custom' ? (
            <div className="flex items-center gap-1">
              <input
                type="date"
                aria-label="From date"
                min={minDate || undefined}
                max={maxDate || undefined}
                value={dateFrom}
                onChange={(e) => onDateFrom(e.target.value)}
                className="sv-input rounded-md px-2"
              />
              <input
                type="date"
                aria-label="To date"
                min={minDate || undefined}
                max={maxDate || undefined}
                value={dateTo}
                onChange={(e) => onDateTo(e.target.value)}
                className="sv-input rounded-md px-2"
              />
            </div>
          ) : null}
          <div className="ml-auto flex items-center gap-1">
            <Chip active={scope === 'map'} onClick={() => onScope('map')}>
              Map
            </Chip>
            <Chip active={scope === 'city'} onClick={() => onScope('city')}>
              City
            </Chip>
          </div>
        </div>
        <div className="sv-panel relative z-10 flex flex-wrap items-center gap-2 rounded-md px-4 py-2.5">
          <div className="flex flex-wrap gap-1">
            {DATASET_OPTIONS.map((opt) => (
              <Chip
                key={opt.value || 'all'}
                rounded="full"
                active={dataset === opt.value}
                onClick={() => onDataset(opt.value)}
              >
                {opt.label}
              </Chip>
            ))}
          </div>
          {categoryChips.length > 0 ? (
            <div className="flex flex-wrap gap-1 border-l border-sv-ink/10 pl-2">
              {categoryChips.map((chip) => {
                const active = Boolean(selectedCategory && selectedCategory.toLowerCase() === chip.value.toLowerCase())
                return (
                  <Chip
                    key={chip.value}
                    rounded="full"
                    title={`Filter by ${chip.label}`}
                    active={active}
                    onClick={() => onCategory(active ? null : chip.value)}
                  >
                    <span className="h-2.5 w-2.5 rounded-full" style={{ background: chip.color }} />
                    {chip.label}
                    <span className={['font-mono text-xs tabular-nums', active ? 'text-sv-on-accent/80' : 'text-sv-muted'].join(' ')}>
                      {chip.count}
                    </span>
                  </Chip>
                )
              })}
            </div>
          ) : null}
          <div className="ml-auto font-mono text-xs tabular-nums text-sv-muted">
            {showing.loading
              ? 'Loading…'
              : showing.m > showing.n
                ? `Showing ${showing.n.toLocaleString()} of ${showing.m.toLocaleString()}`
                : `${showing.n.toLocaleString()} in view`}
          </div>
        </div>
      </div>
    </header>
  )
}
