import React from 'react'

export type DataStatusProps = {
  sha: string
  appTitle?: string
  updatedLine: string | null
  tpsLine: string | null
}

function StatusSep() {
  return (
    <span className="select-none text-sv-ink/30" aria-hidden="true">
      ·
    </span>
  )
}

export const DataStatus: React.FC<DataStatusProps> = ({
  sha,
  appTitle,
  updatedLine,
  tpsLine,
}) => {
  return (
    <p className="flex flex-wrap items-baseline gap-x-2 gap-y-1 text-sm font-medium leading-snug text-sv-ink">
      <span title={appTitle || `App version ${sha}`}>
        <span className="font-bold">App version:</span>{' '}
        <span className="font-mono font-bold tabular-nums text-sv-accent">{sha}</span>
      </span>
      {updatedLine ? (
        <>
          <StatusSep />
          <span>{updatedLine}</span>
        </>
      ) : null}
      {tpsLine ? (
        <>
          <StatusSep />
          <span>{tpsLine}</span>
        </>
      ) : null}
    </p>
  )
}
