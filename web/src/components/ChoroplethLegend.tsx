import React from 'react'
import { CHOROPLETH_RAMP } from '../lib/colors'

type ChoroplethLegendProps = {
  max: number
}

export const ChoroplethLegend: React.FC<ChoroplethLegendProps> = ({ max }) => {
  if (max <= 0) return null
  return (
    <div className="sv-panel pointer-events-auto rounded-md px-3 py-2.5">
      <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-sv-muted">Incidents in window</div>
      <div className="mt-1.5 flex h-2 overflow-hidden rounded-sm">
        {CHOROPLETH_RAMP.map((c) => (
          <div key={c} className="h-full flex-1" style={{ background: c }} />
        ))}
      </div>
      <div className="mt-1 flex justify-between text-[11px] font-semibold tabular-nums text-sv-muted">
        <span>Low</span>
        <span>High · {max.toLocaleString()}</span>
      </div>
    </div>
  )
}
