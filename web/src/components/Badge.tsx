import React from 'react'

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  children: React.ReactNode
  active?: boolean
}

export const Badge: React.FC<BadgeProps> = ({ children, active = false, className = '', ...rest }) => (
  <span
    className={[
      'inline-flex items-center gap-2 rounded-full border bg-sv-paper px-2 py-1 text-xs text-sv-ink',
      active ? 'border-sv-accent bg-sv-accent-soft' : 'border-sv-ink/10',
      className,
    ].join(' ')}
    {...rest}
  >
    {children}
  </span>
)
