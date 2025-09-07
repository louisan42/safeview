import React from 'react'

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  children: React.ReactNode
  active?: boolean
}

export const Badge: React.FC<BadgeProps> = ({ children, active = false, className = '', ...rest }) => (
  <span
    className={[
      'inline-flex items-center gap-2 text-xs px-2 py-1 rounded-full border bg-white',
      active ? 'border-slate-800' : 'border-slate-200',
      'hover:shadow',
      className,
    ].join(' ')}
    {...rest}
  >
    {children}
  </span>
)
