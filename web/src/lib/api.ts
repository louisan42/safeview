import type {
  AnalyticsResponse,
  CompareResponse,
  GeocodeHit,
  IncidentCollection,
  NeighbourhoodCollection,
  NeighbourhoodMatch,
  StatsResponse,
} from './types'

export const API_BASE: string = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8888'

export function incidentsUrl(params: URLSearchParams): string {
  return `${API_BASE}/v1/incidents?${params.toString()}`
}

export function analyticsUrl(params: URLSearchParams): string {
  return `${API_BASE}/v1/analytics?${params.toString()}`
}

export function compareUrl(params: URLSearchParams): string {
  return `${API_BASE}/v1/compare?${params.toString()}`
}

export function choroplethUrl(params: URLSearchParams): string {
  return `${API_BASE}/v1/neighbourhoods/choropleth?${params.toString()}`
}

export function neighbourhoodsUrl(params: URLSearchParams): string {
  return `${API_BASE}/v1/neighbourhoods?${params.toString()}`
}

export function statsUrl(): string {
  return `${API_BASE}/v1/stats`
}

export function geocodeUrl(q: string): string {
  return `${API_BASE}/v1/geocode?q=${encodeURIComponent(q)}`
}

export function neighbourhoodAtUrl(lng: number, lat: number): string {
  return `${API_BASE}/v1/neighbourhoods/at?lng=${encodeURIComponent(String(lng))}&lat=${encodeURIComponent(String(lat))}`
}

export type { AnalyticsResponse, CompareResponse, GeocodeHit, IncidentCollection, NeighbourhoodCollection, NeighbourhoodMatch, StatsResponse }
