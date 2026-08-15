import React from 'react'
import { createPortal } from 'react-dom'
import { fetchJson, humanizeError, isAbortError } from '../lib/http'
import { geocodeUrl, neighbourhoodAtUrl } from '../lib/api'
import type { GeocodeHit, NeighbourhoodMatch } from '../lib/types'

type AddressSearchProps = {
  onLocate: (hit: GeocodeHit, neighbourhood: NeighbourhoodMatch | null) => void
}

type MenuPos = { top: number; left: number; width: number }

export const AddressSearch: React.FC<AddressSearchProps> = ({ onLocate }) => {
  const [q, setQ] = React.useState('')
  const [open, setOpen] = React.useState(false)
  const [hits, setHits] = React.useState<GeocodeHit[]>([])
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [menuPos, setMenuPos] = React.useState<MenuPos | null>(null)
  const abortRef = React.useRef<AbortController | null>(null)
  const boxRef = React.useRef<HTMLDivElement>(null)
  const listRef = React.useRef<HTMLUListElement>(null)

  const updateMenuPos = React.useCallback(() => {
    const el = boxRef.current
    if (!el) return
    const r = el.getBoundingClientRect()
    setMenuPos({ top: r.bottom + 4, left: r.left, width: r.width })
  }, [])

  React.useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      const t = e.target as Node
      if (boxRef.current?.contains(t) || listRef.current?.contains(t)) return
      setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [])

  React.useLayoutEffect(() => {
    if (!open) {
      setMenuPos(null)
      return
    }
    updateMenuPos()
    window.addEventListener('resize', updateMenuPos)
    return () => window.removeEventListener('resize', updateMenuPos)
  }, [open, updateMenuPos])

  React.useEffect(() => {
    const term = q.trim()
    if (term.length < 3) {
      setHits([])
      setError(null)
      return
    }
    const t = window.setTimeout(async () => {
      if (abortRef.current) abortRef.current.abort()
      const controller = new AbortController()
      abortRef.current = controller
      setLoading(true)
      setError(null)
      try {
        const data = await fetchJson<{ results: GeocodeHit[] }>(geocodeUrl(term), controller.signal)
        setHits(data.results || [])
        setOpen(true)
      } catch (err) {
        if (isAbortError(err)) return
        setHits([])
        setError(humanizeError(err) || 'Address lookup failed')
      } finally {
        setLoading(false)
      }
    }, 280)
    return () => window.clearTimeout(t)
  }, [q])

  const pick = async (hit: GeocodeHit) => {
    setQ(hit.label.split(',')[0] || hit.label)
    setOpen(false)
    let neighbourhood: NeighbourhoodMatch | null = null
    try {
      const data = await fetchJson<{ match: NeighbourhoodMatch | null }>(neighbourhoodAtUrl(hit.lng, hit.lat))
      neighbourhood = data.match
    } catch (err) {
      if (!isAbortError(err)) neighbourhood = null
    }
    onLocate(hit, neighbourhood)
  }

  const menu =
    open && menuPos && (hits.length > 0 || error) ? (
      <ul
        ref={listRef}
        className="fixed z-[2000] max-h-64 overflow-auto rounded-md border border-sv-line bg-sv-paper py-1 shadow-paper"
        style={{ top: menuPos.top, left: menuPos.left, width: menuPos.width }}
      >
        {error ? <li className="px-3 py-2 text-sm text-sv-warn">{error}</li> : null}
        {hits.map((hit) => (
          <li key={`${hit.lat},${hit.lng},${hit.label}`}>
            <button
              type="button"
              className="w-full px-3 py-2.5 text-left text-sm text-sv-ink hover:bg-sv-accent-soft"
              onClick={() => pick(hit)}
            >
              {hit.label}
            </button>
          </li>
        ))}
      </ul>
    ) : null

  return (
    <div ref={boxRef} className="relative min-w-0 flex-1">
      <label className="sr-only" htmlFor="sv-address">Search address</label>
      <input
        id="sv-address"
        type="search"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        onFocus={() => hits.length > 0 && setOpen(true)}
        placeholder="Search a Toronto address"
        autoComplete="off"
        className="sv-input w-full rounded-md px-3"
      />
      {loading ? (
        <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 font-mono text-[11px] uppercase tracking-wide text-sv-muted">
          Looking up
        </div>
      ) : null}
      {menu ? createPortal(menu, document.body) : null}
    </div>
  )
}
