import React from 'react'

type BuildStampProps = {
  line: string
  title?: string
}

export const BuildStamp: React.FC<BuildStampProps> = ({ line, title }) => {
  if (!line) return null
  return (
    <p
      className="sv-panel pointer-events-auto whitespace-nowrap rounded-md px-2.5 py-1 text-[11px] leading-snug text-sv-muted"
      title={title || line}
    >
      {line}
    </p>
  )
}
