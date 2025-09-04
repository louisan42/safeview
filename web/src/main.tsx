import React from 'react'
import { createRoot } from 'react-dom/client'
import { MapContainer, TileLayer, GeoJSON, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function App() {
  const [features, setFeatures] = React.useState<any[]>([])
  const [neigh, setNeigh] = React.useState<any | null>(null)

  React.useEffect(() => {
    // initial neighbourhoods (small page)
    fetch(`${API_BASE}/v1/neighbourhoods?limit=100`)
      .then(r => r.json())
      .then(fc => setNeigh(fc))
      .catch(console.error)
  }, [])

  const onMoveEnd = (map: L.Map) => {
    const b = map.getBounds()
    const bbox = `${b.getWest()},${b.getSouth()},${b.getEast()},${b.getNorth()}`
    fetch(`${API_BASE}/v1/incidents?limit=500&bbox=${bbox}`)
      .then(r => r.json())
      .then(fc => setFeatures(fc.features || []))
      .catch(console.error)
  }

  return (
    <div style={{ height: '100%' }}>
      <div className="panel">
        <strong>SafetyView</strong> · Showing incidents in view
      </div>
      <MapContainer
        className="map"
        center={[43.6532, -79.3832]}
        zoom={11}
        whenCreated={(map) => {
          map.on('moveend', () => onMoveEnd(map))
          onMoveEnd(map)
        }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {neigh && (
          <GeoJSON data={neigh as any} style={{ color: '#2266cc', weight: 1, fillOpacity: 0.05 }} />
        )}
        {features.map((f, idx) => {
          if (f.geometry?.type === 'Point') {
            const [lng, lat] = f.geometry.coordinates
            return (
              <Marker key={idx} position={[lat, lng]}>
                <Popup>
                  <div>
                    <div><strong>ID:</strong> {f.properties.id}</div>
                    <div><strong>Dataset:</strong> {f.properties.dataset}</div>
                    <div><strong>Date:</strong> {f.properties.report_date}</div>
                  </div>
                </Popup>
              </Marker>
            )
          }
          return null
        })}
      </MapContainer>
    </div>
  )
}

createRoot(document.getElementById('root')!).render(<App />)
