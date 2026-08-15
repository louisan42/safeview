import React from 'react'

interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode
}

export const IconButton: React.FC<IconButtonProps> = ({ children, className = '', ...rest }) => (
  <button
    className={[
      'fixed top-4 z-[1001] grid h-11 w-11 place-items-center rounded-md',
      'border border-sv-ink/10 bg-sv-paper text-sv-ink shadow-paper',
      'transition-transform duration-150 ease-out hover:bg-sv-paper-2 active:scale-[0.98]',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sv-accent',
      className,
    ].join(' ')}
    {...rest}
  >
    {children}
  </button>
)
