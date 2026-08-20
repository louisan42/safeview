import React from 'react'

type MapStampProps = {
  versionLine: string
  tpsLine: string | null
  title?: string
}

export const MapStamp: React.FC<MapStampProps> = ({ versionLine, tpsLine, title }) => {
  return (
    <div className="pointer-events-none absolute bottom-0 left-1/2 z-[400] -translate-x-1/2">
      <p className="sv-map-stamp" title={title}>
        <span>{versionLine}</span>
        {tpsLine ? (
          <>
            <span className="sv-map-stamp-sep" aria-hidden="true">
              ·
            </span>
            <span>{tpsLine}</span>
          </>
        ) : null}
      </p>
    </div>
  )
}
