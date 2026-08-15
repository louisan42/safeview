import React from 'react'

type ChipProps = {
  active?: boolean
  onClick?: () => void
  children: React.ReactNode
  className?: string
  title?: string
  rounded?: 'md' | 'full'
  disabled?: boolean
}

function chipRadius(rounded: 'md' | 'full'): string {
  switch (rounded) {
    case 'full':
      return 'rounded-full'
    case 'md':
      return 'rounded-md'
    default: {
      const _never: never = rounded
      return _never
    }
  }
}

export const Chip: React.FC<ChipProps> = ({
  active = false,
  onClick,
  children,
  className = '',
  title,
  rounded = 'md',
  disabled = false,
}) => {
  return (
    <button
      type="button"
      title={title}
      disabled={disabled}
      onClick={onClick}
      className={[
        'sv-chip',
        chipRadius(rounded),
        active
          ? 'border border-transparent bg-sv-accent text-sv-on-accent hover:bg-sv-accent-strong'
          : 'border border-sv-ink/10 bg-transparent text-sv-ink hover:bg-sv-ink/[0.04]',
        disabled ? 'opacity-40' : '',
        className,
      ].join(' ')}
    >
      {children}
    </button>
  )
}
