import React from 'react'

type EmptyStateProps = {
  outsideRange: boolean
  minDate: string | null
  maxDate: string | null
  onJump: () => void
}

export const EmptyState: React.FC<EmptyStateProps> = ({ outsideRange, minDate, maxDate, onJump }) => {
  return (
    <div className="sv-panel pointer-events-auto max-w-sm rounded-md px-5 py-4 text-center">
      <div className="font-display text-lg font-bold tracking-tight text-sv-ink">
        {outsideRange ? 'This window is outside the available data' : 'No incidents in the current view'}
      </div>
      {minDate && maxDate ? (
        <div className="mt-1 font-mono text-xs tabular-nums text-sv-muted">
          Data available {minDate} → {maxDate}
        </div>
      ) : null}
      <button
        type="button"
        onClick={onJump}
        className="mt-3 inline-flex h-11 min-w-[44px] items-center justify-center rounded-md bg-sv-accent px-4 text-sm font-semibold text-sv-on-accent transition-transform duration-150 ease-out hover:bg-sv-accent-strong active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sv-accent focus-visible:ring-offset-2 focus-visible:ring-offset-sv-paper"
      >
        Jump to latest data
      </button>
    </div>
  )
}
