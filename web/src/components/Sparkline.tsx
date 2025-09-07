import React from 'react'

export const Sparkline: React.FC<{ data: number[]; width?: number; height?: number; stroke?: string; className?: string }>
  = ({ data, width = 96, height = 24, stroke = '#2563eb', className }) => {
  if (!data || data.length === 0) return null
  const max = Math.max(...data)
  const min = Math.min(...data)
  const range = max - min || 1
  const stepX = data.length > 1 ? width / (data.length - 1) : width
  const points = data.map((v, i) => {
    const x = i * stepX
    const y = height - ((v - min) / range) * height
    return `${x},${y}`
  }).join(' ')
  return (
    <svg className={className} width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <polyline fill="none" stroke={stroke} strokeWidth="2" points={points} />
    </svg>
  )
}
