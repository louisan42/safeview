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
        'fixed bottom-0 left-0 top-0 z-[999] overflow-y-auto bg-sv-paper',
        'border-r border-sv-ink/10 shadow-paper',
        'transition-transform duration-200 ease-out',
        className || '',
      ].join(' ')}
      style={{ width, transform: open ? 'translateX(0)' : `translateX(-${width}px)` }}
    >
      <div className="h-full p-5">{children}</div>
    </div>
  )
}
