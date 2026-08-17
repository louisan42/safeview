import React from 'react'
import { niceMax, xTickIndexes, yTicks, type ChartSeries } from '../lib/chart'

type TrendChartProps = {
  categories: string[]
  series: ChartSeries[]
  height?: number
  yMax?: number
  xTicks?: string[]
  compact?: boolean
  ariaLabel: string
}

function polylinePoints(
  values: number[],
  width: number,
  height: number,
  padL: number,
  padR: number,
  padT: number,
  padB: number,
  max: number,
): string {
  const plotW = Math.max(1, width - padL - padR)
  const plotH = Math.max(1, height - padT - padB)
  const n = values.length
  return values
    .map((value, i) => {
      const x = n === 1 ? padL + plotW / 2 : padL + (i / (n - 1)) * plotW
      const y = padT + plotH - (value / max) * plotH
      return `${x},${y}`
    })
    .join(' ')
}

export const TrendChart: React.FC<TrendChartProps> = ({
  categories,
  series,
  height = 220,
  yMax,
  xTicks,
  compact = false,
  ariaLabel,
}) => {
  const wrapRef = React.useRef<HTMLDivElement>(null)
  const [width, setWidth] = React.useState(320)
  const [hover, setHover] = React.useState<number | null>(null)

  React.useEffect(() => {
    const el = wrapRef.current
    if (!el) return
    const apply = (next: number) => {
      const rounded = Math.max(160, Math.round(next))
      setWidth((prev) => (prev === rounded ? prev : rounded))
    }
    apply(el.clientWidth)
    const observer = new ResizeObserver((entries) => {
      const entry = entries[0]
      if (entry) apply(entry.contentRect.width)
    })
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  const n = categories.length
  const rawMax = Math.max(yMax ?? 0, ...series.flatMap((s) => s.values), 0)
  const max = niceMax(rawMax)
  const padL = compact ? 28 : 36
  const padR = 10
  const padT = compact ? 8 : 12
  const padB = compact ? 20 : 28
  const plotW = Math.max(1, width - padL - padR)
  const plotH = Math.max(1, height - padT - padB)
  const ticksY = yTicks(max, compact ? 3 : 4)
  const ticksX = xTickIndexes(n)
  const labels = xTicks || categories

  const xAt = (i: number) => (n <= 1 ? padL + plotW / 2 : padL + (i / Math.max(n - 1, 1)) * plotW)

  const onMove = (event: React.MouseEvent<SVGSVGElement>) => {
    if (n === 0) return
    const rect = event.currentTarget.getBoundingClientRect()
    const x = event.clientX - rect.left
    if (n === 1) {
      setHover(0)
      return
    }
    const t = (x - padL) / plotW
    const i = Math.min(n - 1, Math.max(0, Math.round(t * (n - 1))))
    setHover(i)
  }

  if (n === 0 || series.length === 0) {
    return (
      <div
        ref={wrapRef}
        className="flex items-center justify-center text-sm text-sv-muted"
        style={{ height }}
      >
        No incidents in this window
      </div>
    )
  }

  const tip = hover !== null ? series.map((s) => `${s.name}: ${s.values[hover] ?? 0}`) : []

  return (
    <div ref={wrapRef} className="relative w-full">
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={ariaLabel}
        className="block max-w-full"
        onMouseMove={onMove}
        onMouseLeave={() => setHover(null)}
      >
        {ticksY.map((tick) => {
          const y = padT + plotH - (tick / max) * plotH
          return (
            <g key={`y-${tick}`}>
              <line x1={padL} x2={width - padR} y1={y} y2={y} stroke="rgba(41,37,36,0.08)" strokeWidth="1" />
              <text
                x={padL - 6}
                y={y + 3}
                textAnchor="end"
                className="fill-sv-muted"
                style={{ fontSize: compact ? 9 : 10, fontFamily: 'Nunito, sans-serif' }}
              >
                {tick}
              </text>
            </g>
          )
        })}
        {ticksX.map((i) => (
          <text
            key={`x-${i}`}
            x={xAt(i)}
            y={height - 6}
            textAnchor="middle"
            className="fill-sv-muted"
            style={{ fontSize: compact ? 9 : 10, fontFamily: 'Nunito, sans-serif' }}
          >
            {labels[i] || ''}
          </text>
        ))}
        {series.map((s) => (
          <polyline
            key={s.name}
            fill="none"
            stroke={s.color}
            strokeWidth={compact ? 1.75 : 2.25}
            strokeLinejoin="round"
            strokeLinecap="round"
            points={polylinePoints(s.values, width, height, padL, padR, padT, padB, max)}
          />
        ))}
        {hover !== null ? (
          <g>
            <line
              x1={xAt(hover)}
              x2={xAt(hover)}
              y1={padT}
              y2={padT + plotH}
              stroke="rgba(41,37,36,0.28)"
              strokeWidth="1"
            />
            {series.map((s) => {
              const value = s.values[hover] ?? 0
              const y = padT + plotH - (value / max) * plotH
              return <circle key={`${s.name}-dot`} cx={xAt(hover)} cy={y} r={3.5} fill={s.color} />
            })}
          </g>
        ) : null}
      </svg>
      {hover !== null ? (
        <div
          className="pointer-events-none absolute z-10 rounded-md border border-sv-ink/10 bg-sv-paper px-2 py-1.5 text-xs text-sv-ink shadow-paper"
          style={{
            left: Math.min(width - 160, Math.max(8, xAt(hover) + 8)),
            top: 8,
          }}
        >
          <div className="font-semibold">{labels[hover]}</div>
          {tip.map((line) => (
            <div key={line} className="tabular-nums text-sv-muted">
              {line}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  )
}
