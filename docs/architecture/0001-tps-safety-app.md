# Architecture Plan: Toronto Public Safety Map App

Below is a concise, implementation-ready architecture plan for a user-friendly web app leveraging Toronto Police Service public safety/open data. It emphasizes modularity and future microservice conversion.

## Product Goals

- **User-friendly map**: Users enter an address; map pans/zooms and overlays neighborhood crime metrics.
- **Neighborhood crime index**: Intuitive, normalized index per neighborhood and time range.
- **Explainability**: Show underlying counts, trends, and categories backing the index.
- **Performance**: Snappy geocoding and map interactivity on commodity devices.
- **Modular**: Clean boundaries; easy path to microservices.

## Non-Goals (initial)

- **Real-time dispatch feeds**
- **Predictive policing**
- **User accounts/SSO** (phase 2)

## Key Features (MVP)

- **Address search**: Autocomplete + geocoding.
- **Neighborhood lookup**: Reverse geocode to neighborhood/ward/BIA boundary.
- **Crime index**: Composite score with category weights and recency decay.
- **Map layers**: Choropleth for index; markers/heatmap for incidents.
- **Time filter**: Last 30/90/365 days.
- **Category filters**: Violent, property, traffic, etc.
- **Details drawer**: Trend sparkline, category breakdown, sources.

## UX Notes

- **Landing**: Prominent address search bar; Toronto extent default view.
- **Accessibility**: Color-safe choropleth; keyboard nav; ARIA labels.
- **Mobile-first**: Bottom sheet for details; performant clustering.

## Data Sources

- **Toronto Police Service / City of Toronto Open Data** (CKAN):
  - Occurrence/crime incidents by date, category, approximate location (often rounded).
  - Neighborhood/ward boundaries (GeoJSON/SHP).
- **CKAN APIs**:
  - package_show for metadata.
  - datastore_search/datastore_search_sql for tabular data.
- **Notes**: TPS sometimes releases CSVs/GeoJSON through City CKAN. Validate schema/fields and update ingestion accordingly.

## Crime Index Method

- **Inputs**: Incident counts by category per neighborhood per time bucket (e.g., weekly).
- **Weighting**: Category weights (e.g., violent 1.0, property 0.6, other 0.3).
- **Recency decay**: Exponential decay for last N months (e.g., half-life 90 days).
- **Normalization**: Per 1,000 residents (requires population per neighborhood) and z-score normalization to 0–100 index.
- **Transparency**: Show raw counts and weights; publish formula in `docs/`.

## High-Level Architecture

- **Frontend (Web)**:
  - Next.js (React + TypeScript), ISR/SSR for SEO and speed.
  - MapLibre GL JS or Leaflet for open-source mapping.
  - UI: Radix UI/Shadcn or MUI; TailwindCSS.
- **Backend API**:
  - Option A: Node.js + TypeScript (NestJS/Fastify) for one-language stack.
  - Option B: Python FastAPI for data/analytics ergonomics.
  - Serve REST/JSON endpoints for search, index, and map data.
- **Data/ETL**:
  - Ingestion workers to pull from CKAN, validate, geospatially process, and store.
  - Batch schedule (e.g., daily) with on-demand refresh.
- **Storage**:
  - Postgres + PostGIS for spatial joins and tiles precomputation.
  - Redis for caching geocoding and hot queries.
  - Object storage (S3-compatible) for static tiles/exports if needed.
- **Geocoding**:
  - Open: Nominatim (OSM) or Pelias; or external managed (Mapbox/Google) if needed.
  - Cache results server-side to control cost/latency.
- **Map Tiles**:
  - Vector tiles via open providers (MapTiler, Stadia) or self-hosted tile server.
- **Observability**:
  - Logging: structured JSON logs.
  - Metrics: Prometheus + Grafana.
  - Error tracking: Sentry.

## Service Boundaries (Modular, Microservice-Ready)

- **api-gateway**:
  - Routes, auth (future), rate limiting, response caching.
- **geocoder-service**:
  - Forward/reverse geocoding with cache and provider fallback.
- **ingestion-service**:
  - CKAN pulls, schema validation, deduplication, write to PostGIS raw tables.
- **analytics-service**:
  - Crime index computation, aggregation jobs, stores results in materialized tables.
- **map-service**:
  - Serves neighborhood polygons, tiles, and incident layers; pre-generates or on-the-fly.
- **frontend**:
  - Static assets + SSR server.

Start as a modular monorepo with clear package boundaries, then split services when scaling is needed.

## API Endpoints (v1)

- **GET `/v1/search?q=address`** → geocode results.
- **GET `/v1/point-to-neighborhood?lat=..&lng=..`** → neighborhood id + meta.
- **GET `/v1/neighborhoods/:id/index?from=&to=&categories=`** → index + breakdown + trend.
- **GET `/v1/neighborhoods/choropleth?from=&to=&categories=`** → GeoJSON with index for all neighborhoods.
- **GET `/v1/incidents?bbox=&from=&to=&categories=&limit=&cursor=`** → paginated incidents for map.
- **GET `/v1/metadata`** → dataset versions, last refresh.

## Data Model (Postgres/PostGIS)

- **tables**:
  - `neighborhoods(id, name, population, geom MULTIPOLYGON)`
  - `incidents(id, occurred_at, category, geom POINT, neighborhood_id, source_id, properties JSONB)`
  - `indices(neighborhood_id, period_start, period_end, index_value, counts JSONB, meta JSONB)`
  - `sources(id, name, version, pulled_at, raw_url, checksum)`
- **indexes**:
  - GIST on `neighborhoods.geom`, `incidents.geom`.
  - BTREE on `occurred_at`, `category`, `neighborhood_id`.
- **materialized views**:
  - `mv_incidents_agg_<period>` with refresh job.
  - `mv_indices_latest`.

## ETL Pipeline

- **Extractor**: CKAN client pulls latest records incrementally (by modified timestamp or max(id)).
- **Transformer**:
  - Validate schema, map categories to internal taxonomy.
  - Spatial join: assign `neighborhood_id` via `ST_Contains`.
  - Round locations if required by policy.
- **Loader**: Upsert to `incidents`; refresh MVs; recompute indices.
- **Scheduler**: GitHub Actions/Cron/K8s CronJob; cadence daily.

## Security & Privacy

- **PII**: Use only publicly released fields. Do not attempt de-anonymization.
- **Rate limiting**: API gateway level (e.g., 100 rpm per IP).
- **CORS**: Restrictive by default; allow only the app origin.
- **Secrets**: Use environment-based secret manager (Doppler/1Password/Vault/SSM).
- **Compliance**: Respect TPS/City open data licenses and attribution.

## Performance

- **Caching**: 
  - CDN for static/tiles.
  - Redis for common geocodes and `choropleth` responses.
- **Pagination**:
  - Incidents endpoint cursor-based.
- **Precompute**:
  - Index and aggregates in advance per time bucket.

## Testing Strategy

- **Unit**: Index formula, ETL mappers, geocoder adapters.
- **Integration**: Database queries, spatial joins against a seed dataset.
- **E2E**: Headless tests for address → index flow.
- **Data checks**: Row counts, null rate, category coverage thresholds.

## CI/CD

- **Monorepo**: TurboRepo or Nx for TS stack; Poetry/UV if Python included.
- **Actions**:
  - Lint/typecheck/test on PR.
  - DB migrations via Prisma (TS) or Alembic (Python).
  - Versioned deploy to staging/prod; feature preview environments.

## Tech Stack Recommendations

- **Primary Option (one-language)**:
  - Frontend: Next.js + TypeScript
  - Backend: NestJS (Fastify) + TypeScript
  - ORM: Prisma
  - DB: Postgres + PostGIS
  - Map: MapLibre GL, Tile provider: MapTiler (open-friendly)
  - Geocoding: Nominatim with server-side caching
- **Alternative (data-heavy)**:
  - Backend: FastAPI (Python)
  - ETL/Analytics: Python (Pandas/GeoPandas, Shapely) with async workers (Celery/RQ)
  - Frontend: same as above

Both are solid; choose by team skill. For microservices, either stack deploys well on Kubernetes.

## Milestones

- **M0**: Repo setup, envs, DB with PostGIS, boundary data loaded.
- **M1**: ETL ingest of incidents; geocoding service with cache.
- **M2**: Index algorithm implemented; materialized aggregates.
- **M3**: Frontend map with search, choropleth, details drawer.
- **M4**: API hardening, caching, observability, accessibility pass.
- **M5**: Production rollout with docs and monitoring.

## Open Questions

- **Exact TPS datasets**: Confirm fields, update taxonomy mapping.
- **Population data source**: Latest neighborhood population stats for normalization.
- **Tile hosting**: Self-host vs managed (cost/perf).
- **Attribution requirements**: For OSM, City of Toronto, TPS.

## Next Steps

- Choose backend stack: TypeScript (NestJS) or Python (FastAPI).
- Approve index formula defaults (weights, decay, normalization).
- Begin dataset research and schema mapping.
