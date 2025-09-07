import React from 'react'

interface MiniBarsProps {
  data: Array<{ label?: string; count: number }>
  height?: number
  barColor?: string
  className?: string
}

export const MiniBars: React.FC<MiniBarsProps> = ({ data, height = 28, barColor = '#2563eb', className }) => {
  if (!data || data.length === 0) return null
  const max = Math.max(...data.map(d => d.count)) || 1
  return (
    <div className={className} style={{ height }}>
      <div className="flex items-end gap-0.5 h-full">
        {data.map((d, i) => {
          const h = Math.max(2, Math.round((d.count / max) * height))
          return (
            <div key={i} title={(d.label || '') + (d.label ? ': ' : '') + d.count}
                 style={{ height: h, background: barColor, width: 6 }}
                 className="rounded-sm" />
          )
        })}
      </div>
    </div>
  )
}
