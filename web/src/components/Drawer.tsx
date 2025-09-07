import React from 'react'

interface DrawerProps {
  open: boolean
  width?: number
  className?: string
  children: React.ReactNode
}

export const Drawer: React.FC<DrawerProps> = ({ open, width = 380, className, children }) => {
  return (
    <div
      className={[
        'fixed top-0 bottom-0 left-0 z-[999] bg-white/95 backdrop-saturate-150 backdrop-blur-md',
        'border-r border-slate-200 shadow-2xl overflow-y-auto',
        'transition-transform duration-300 ease-in-out',
        className || ''
      ].join(' ')}
      style={{ width, transform: open ? 'translateX(0)' : `translateX(-${width}px)` }}
    >
      <div className="p-4 h-full">
        {children}
      </div>
    </div>
  )
}
