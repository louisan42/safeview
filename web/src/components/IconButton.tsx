import React from 'react'

interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode
}

export const IconButton: React.FC<IconButtonProps> = ({ children, className = '', ...rest }) => (
  <button
    className={[
      'fixed top-4 z-[1001] w-12 h-12 rounded-full',
      'border border-slate-200 bg-white shadow-xl grid place-items-center',
      'hover:shadow-2xl transition-all duration-200',
      'hover:scale-105 active:scale-95',
      className,
    ].join(' ')}
    {...rest}
  >
    {children}
  </button>
)
