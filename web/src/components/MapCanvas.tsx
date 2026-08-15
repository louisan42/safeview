import React from 'react'
import { GeoJSON, MapContainer, Marker, Popup, TileLayer, ZoomControl, useMap, useMapEvents } from 'react-leaflet'
import MarkerClusterGroup from 'react-leaflet-cluster'
import L from 'leaflet'
import type { FeatureCollection as GJFeatureCollection, Feature as GJFeature } from 'geojson'
import { ACCENT, colorForIncident, choroplethColor, choroplethOpacity } from '../lib/colors'
import { categoryLabel } from '../lib/labels'
import { formatDay } from '../lib/dates'
import type { IncidentFeature, NeighbourhoodCollection, NeighbourhoodFeature } from '../lib/types'

const TORONTO: L.LatLngExpression = [43.6532, -79.3832]

type MapCanvasProps = {
  choropleth: NeighbourhoodCollection | null
  incidents: IncidentFeature[]
  selectedCode: string | null
  hoodNames: Map<string, string>
  onReady: (map: L.Map) => void
  onMoveEnd: (map: L.Map) => void
  onSelectHood: (feature: NeighbourhoodFeature) => void
  flyTo: { lat: number; lng: number; zoom?: number } | null
}

const iconFor = (f: IncidentFeature) => {
  const color = colorForIncident(f)
  const html = `<span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:${color};box-shadow:0 0 0 2px #f7f4ee,0 1px 2px rgba(41,37,36,.35);"></span>`
  return L.divIcon({ className: 'sv-pin', html, iconSize: [12, 12], iconAnchor: [6, 6] })
}

const clusterIcon = (cluster: { getChildCount: () => number }) => {
  const n = cluster.getChildCount()
  return L.divIcon({
    html: `<span>${n}</span>`,
    className: 'sv-cluster',
    iconSize: L.point(36, 36, true),
  })
}

const MapEvents: React.FC<{ onReady: (map: L.Map) => void; onMoveEnd: (map: L.Map) => void }> = ({ onReady, onMoveEnd }) => {
  const map = useMapEvents({
    moveend() {
      onMoveEnd(map)
    },
  })
  React.useEffect(() => {
    onReady(map)
  }, [map, onReady])
  return null
}

const FlyTo: React.FC<{ target: { lat: number; lng: number; zoom?: number } | null }> = ({ target }) => {
  const map = useMap()
  React.useEffect(() => {
    if (!target) return
    map.flyTo([target.lat, target.lng], target.zoom ?? 15, { duration: 0.8 })
  }, [map, target])
  return null
}

function popupText(f: IncidentFeature, hoodNames: Map<string, string>): string {
  const cat = categoryLabel(f.properties.mci_category || f.properties.dataset)
  const offence = (f.properties.offence || '').trim()
  const offenceBit = offence && offence.toLowerCase() !== cat.toLowerCase() ? ` — ${offence}` : ''
  const day = formatDay(f.properties.report_datetime || f.properties.report_date)
  const hood =
    hoodNames.get(f.properties.hood_158 || '') || f.properties.hood_158 || ''
  return [cat + offenceBit, day, hood].filter(Boolean).join(' · ')
}

export const MapCanvas: React.FC<MapCanvasProps> = ({
  choropleth,
  incidents,
  selectedCode,
  hoodNames,
  onReady,
  onMoveEnd,
  onSelectHood,
  flyTo,
}) => {
  const maxCount = React.useMemo(() => {
    const counts = (choropleth?.features || []).map((f) => Number(f.properties.incident_count || 0))
    return Math.max(0, ...counts)
  }, [choropleth])

  const styleFeature = React.useCallback(
    (feature?: NeighbourhoodFeature) => {
      const count = Number(feature?.properties.incident_count || 0)
      const selected = feature?.properties.area_long_code === selectedCode
      return {
        color: selected ? ACCENT : 'rgba(41, 37, 36, 0.38)',
        weight: selected ? 2.2 : 1.25,
        opacity: 1,
        fillColor: choroplethColor(count, maxCount),
        fillOpacity: choroplethOpacity(count),
        smoothFactor: 0.8,
      }
    },
    [maxCount, selectedCode],
  )

  const onEach = React.useCallback(
    (feature: NeighbourhoodFeature, layer: L.Layer) => {
      layer.on({
        click: (e) => {
          L.DomEvent.stopPropagation(e)
          onSelectHood(feature)
        },
      })
    },
    [onSelectHood],
  )

  return (
    <MapContainer className="h-full w-full bg-sv-paper" center={TORONTO} zoom={11} zoomControl={false} preferCanvas>
      <MapEvents onReady={onReady} onMoveEnd={onMoveEnd} />
      <FlyTo target={flyTo} />
      <ZoomControl position="bottomleft" />
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
      />
      {choropleth ? (
        <GeoJSON
          key={`${maxCount}-${selectedCode}-${choropleth.features.length}`}
          data={choropleth as unknown as GJFeatureCollection}
          style={styleFeature as L.StyleFunction}
          onEachFeature={onEach as (feature: GJFeature, layer: L.Layer) => void}
        />
      ) : null}
      <MarkerClusterGroup
        chunkedLoading
        showCoverageOnHover={false}
        spiderfyOnMaxZoom
        maxClusterRadius={48}
        iconCreateFunction={clusterIcon}
      >
        {incidents.map((f, idx) => {
          if (f.geometry?.type !== 'Point' || !Array.isArray(f.geometry.coordinates)) return null
          const coords = f.geometry.coordinates as number[]
          const lng = coords[0]
          const lat = coords[1]
          return (
            <Marker key={String(f.properties.id ?? idx)} position={[lat, lng]} icon={iconFor(f)}>
              <Popup>
                <div className="sv-popup">{popupText(f, hoodNames)}</div>
              </Popup>
            </Marker>
          )
        })}
      </MarkerClusterGroup>
    </MapContainer>
  )
}
