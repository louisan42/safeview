import React from 'react'

interface TooltipProps {
  text: string
  children: React.ReactNode
  className?: string
}

export const Tooltip: React.FC<TooltipProps> = ({ text, children, className }) => {
  return (
    <span className={["relative group inline-flex", className || ''].join(' ')}>
      {children}
      <span className="pointer-events-none absolute left-1/2 top-full z-[1000] mt-1 -translate-x-1/2 whitespace-nowrap rounded-md bg-slate-900 px-2 py-1 text-xs text-white opacity-0 shadow group-hover:opacity-100 transition-opacity">
        {text}
      </span>
    </span>
  )
}
