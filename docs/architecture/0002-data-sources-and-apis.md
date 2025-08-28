# Data Sources and APIs: Toronto Public Safety App

This document tracks concrete datasets, API endpoints, schemas, and sample queries for the app. It will evolve as we validate fields and availability.

## Summary of Findings (current)

- **City of Toronto Open Data (CKAN)**
  - Several legacy datasets are marked **Retired** (e.g., Major Crime Indicators, Neighbourhoods, Neighbourhood Crime Rates).
  - CKAN endpoint patterns remain useful for other civic datasets (e.g., demographics).
- **Toronto Police Service Public Safety Data Portal (ArcGIS)**
  - Active operational datasets are hosted on TPS ArcGIS Open Data.
  - Expect ArcGIS FeatureServer/MapServer endpoints, with field schemas accessible via the REST API.

## Priority Datasets

- **Incidents / Crime categories**
  - Source: TPS ArcGIS Open Data catalogue
  - Portal: https://opendata-torontops.opendata.arcgis.com/search?collection=Dataset
  - Notes: Look for Major Crime Indicators (MCI) equivalents or incident-level layers (assault, break-and-enter, robbery, auto theft, theft over, homicide), shootings, and traffic safety datasets.

- **Neighbourhood boundaries**
  - Source: TPS or City Open Data (current authoritative polygons)
  - If City’s older `Neighbourhoods` dataset is retired, check for updated boundary layers (e.g., 158 neighbourhoods 2020+ revision) on the City portal or TPS portal.

- **Population / Demographics (for normalization)**
  - Source: City of Toronto CKAN (Neighbourhood Profiles)
  - CKAN dataset: https://ckan0.cf.opendata.inter.prod-toronto.ca/en_AU/dataset/neighbourhood-profiles

## API Patterns

### CKAN (City of Toronto)

- **Package metadata**
  - GET: `/api/3/action/package_show?id=<dataset_name>`
- **Resource data**
  - GET: `/api/3/action/datastore_search?resource_id=<resource_id>&limit=5`
  - GET (SQL): `/api/3/action/datastore_search_sql?sql=<SQL-encoded>`

Example (pseudocode):
```
GET https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_show?id=neighbourhood-profiles
GET https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/datastore_search?resource_id=<RID>&limit=5
```

### ArcGIS (TPS Open Data)

- **Service metadata**
  - `.../FeatureServer` → service; `.../FeatureServer/<layerId>` → layer schema
  - Append `?f=pjson` for JSON metadata.
- **Queries**
  - `.../FeatureServer/<layerId>/query` with params:
    - `where=1=1` (filter)
    - `outFields=*` (fields)
    - `geometry=<bbox or point>` + `inSR=4326`
    - `spatialRel=esriSpatialRelIntersects`
    - `returnGeometry=true`
    - `f=geojson` or `f=json`

Example (pseudocode):
```
GET https://<tps-arcgis-host>/FeatureServer/<layerId>?f=pjson
GET https://<tps-arcgis-host>/FeatureServer/<layerId>/query?where=1%3D1&outFields=*&f=geojson&resultRecordCount=100
```

## Validated TPS FeatureServer Endpoints (incident-level)

- __Robbery Open Data__
  - Service: https://services.arcgis.com/S9th0jAJ7bqgIRjw/arcgis/rest/services/Robbery_Open_Data/FeatureServer
  - Layer 0 schema: https://services.arcgis.com/S9th0jAJ7bqgIRjw/arcgis/rest/services/Robbery_Open_Data/FeatureServer/0?f=pjson
  - Key fields: OBJECTID, EVENT_UNIQUE_ID, REPORT_DATE, OCC_DATE, REPORT_YEAR, REPORT_MONTH, REPORT_DAY, REPORT_DOW, REPORT_HOUR, OCC_YEAR, OCC_MONTH, OCC_DAY, OCC_DOW, OCC_HOUR, DIVISION, LOCATION_TYPE, PREMISES_TYPE, UCR_CODE, UCR_EXT, OFFENCE, MCI_CATEGORY, HOOD_158, NEIGHBOURHOOD_158, HOOD_140, NEIGHBOURHOOD_140, LONG_WGS84, LAT_WGS84

- __Theft Over Open Data__
  - Service: https://services.arcgis.com/S9th0jAJ7bqgIRjw/arcgis/rest/services/Theft_Over_Open_Data/FeatureServer
  - Layer 0 schema: https://services.arcgis.com/S9th0jAJ7bqgIRjw/arcgis/rest/services/Theft_Over_Open_Data/FeatureServer/0?f=pjson
  - Key fields: same structure as above (confirm identical list in schema)

- __Break and Enter Open Data__
  - Service: https://services.arcgis.com/S9th0jAJ7bqgIRjw/arcgis/rest/services/Break_and_Enter_Open_Data/FeatureServer
  - Layer 0 schema: https://services.arcgis.com/S9th0jAJ7bqgIRjw/arcgis/rest/services/Break_and_Enter_Open_Data/FeatureServer/0?f=pjson
  - Key fields: same structure as above (confirm identical list in schema)

### Example queries (ArcGIS FeatureServer)

- __Latest 30 days within a bbox (GeoJSON)__
  ```text
  GET {SERVICE}/FeatureServer/0/query
    ?where=REPORT_DATE%20%3E%3D%20CURRENT_TIMESTAMP%20-%20INTERVAL%20'30'%20DAY
    &outFields=EVENT_UNIQUE_ID,REPORT_DATE,OFFENCE,MCI_CATEGORY,HOOD_158,LONG_WGS84,LAT_WGS84
    &geometry=-79.65,43.60,-79.10,43.85
    &geometryType=esriGeometryEnvelope
    &inSR=4326
    &spatialRel=esriSpatialRelIntersects
    &returnGeometry=true
    &f=geojson
  ```
  Replace `{SERVICE}` with one of the service URLs above.

- __Count by neighbourhood (HOOD_158) over a date range__
  ```text
  GET {SERVICE}/FeatureServer/0/query
    ?where=REPORT_DATE%20BETWEEN%20TIMESTAMP%20'2024-01-01%2000%3A00%3A00'%20AND%20TIMESTAMP%20'2024-12-31%2023%3A59%3A59'
    &groupByFieldsForStatistics=HOOD_158
    &outStatistics=[{"statisticType":"count","onStatisticField":"OBJECTID","outStatisticFieldName":"count"}]
    &outFields=HOOD_158
    &f=json
  ```

- __Sample feature fetch (first 100)__
  ```text
  GET {SERVICE}/FeatureServer/0/query?where=1%3D1&outFields=*&resultRecordCount=100&f=json
  ```

### Neighbourhoods (authoritative polygons) — candidates to confirm

- __City of Toronto Neighbourhoods (older 140)__
  - Layer: https://gis.toronto.ca/arcgis/rest/services/cot_geospatial26/FeatureServer/9
  - Note: Appears to describe 140 neighbourhoods (pre-2021). Use with caution.

- __Neighbourhoods 158 candidates (ArcGIS items)__
  - https://www.arcgis.com/home/item.html?id=5913f337900949d9be150ac6f203eefb (Toronto Neighbourhoods n158 v3_4)
  - https://www.arcgis.com/home/item.html?id=ed8f16dfc2a64a23a462a30ded32bda1
  - https://www.arcgis.com/home/item.html?id=03b29003295d4dbfb0f53347942fb58e

- __Next action__: identify the current authoritative FeatureServer polygon layer that exposes `HOOD_158`/`AREA_NAME` (or equivalent) and CRS=4326/102100; confirm update cadence and attribution.

## Neighbourhood Code Mapping (HOOD_158 ⇄ AREA codes)

- __Goal__: verify and document mapping between TPS `HOOD_158` and City `AREA_LONG_CODE`/`AREA_SHORT_CODE`.

- __Distinct values (TPS incidents)__
  ```text
  GET {TPS_SERVICE}/FeatureServer/0/query
    ?where=1%3D1
    &returnDistinctValues=true
    &outFields=HOOD_158
    &orderByFields=HOOD_158
    &f=json
  ```

- __Distinct values (City neighbourhoods)__
  ```text
  GET https://services3.arcgis.com/b9WvedVPoizGfvfD/arcgis/rest/services/COTGEO_CENSUS_NEIGHBORHOOD/FeatureServer/0/query
    ?where=1%3D1
    &returnDistinctValues=true
    &outFields=AREA_LONG_CODE,AREA_SHORT_CODE,AREA_NAME
    &orderByFields=AREA_LONG_CODE
    &f=json
  ```

- __PostGIS mapping table__
  ```sql
  CREATE TABLE IF NOT EXISTS hood158_area_map (
    hood_158 text PRIMARY KEY,
    area_long_code text NOT NULL,
    area_short_code text,
    area_name text,
    note text
  );
  ```

- __Checklist__
  - Pull distincts from both sources; confirm 158 codes on each side.
  - If exact match (e.g., `HOOD_158` == `AREA_LONG_CODE`), auto-populate mapping.
  - Otherwise, curate differences and record in `note`.
  - Store mapping CSV in repo and load into DB for fast joins.

## Next Research Actions

- **Locate active TPS incident layers** on the ArcGIS portal and record:
  - Dataset name, description, license, update frequency
  - FeatureServer URL, layerId(s)
  - Key fields: occurrence date/time, category/type, x/y or geometry, anonymization notes
- **Confirm authoritative neighbourhood polygons** and capture the service URL.
- **Extract population fields** from Neighbourhood Profiles (resource id, field names, year).
- **Draft sample queries** for:
  - Date-range filtered incidents by bbox
  - Incident aggregation by neighbourhood (server-side where possible)
  - Choropleth-ready join of neighbourhood polygons with index values

## Integration Notes

- **Geocoding**: Continue with Nominatim/Pelias; store `lat/lng` then use `point-in-polygon` against neighbourhoods (PostGIS `ST_Contains`).
- **Rate limiting**: Respect TPS portal usage guidelines; mirror critical layers into our PostGIS via ETL for performance and resilience.
- **Attribution**: Include OSM, City of Toronto, and TPS attributions in map UI and docs.

## Open Questions (to resolve)

- Do TPS incident layers provide sufficient spatial resolution and timeliness for our index?
- Which neighbourhood boundary version is current (and aligns with Profiles)?
- Any TPS-specific aggregation layers that simplify index computation?

## Join & Choropleth Templates

- __ArcGIS: count incidents by neighbourhood code (server-side)__
  ```text
  GET {SERVICE}/FeatureServer/0/query
    ?where=REPORT_DATE%20BETWEEN%20TIMESTAMP%20'2024-01-01%2000:00:00'%20AND%20TIMESTAMP%20'2024-12-31%2023:59:59'
    &groupByFieldsForStatistics=HOOD_158
    &outStatistics=[{"statisticType":"count","onStatisticField":"OBJECTID","outStatisticFieldName":"cnt"}]
    &outFields=HOOD_158
    &f=json
  ```

- __ArcGIS: fetch neighbourhood polygons (GeoJSON) for client join__
  ```text
  GET https://services3.arcgis.com/b9WvedVPoizGfvfD/arcgis/rest/services/COTGEO_CENSUS_NEIGHBORHOOD/FeatureServer/0/query
    ?where=1%3D1
    &outFields=AREA_LONG_CODE,AREA_SHORT_CODE,AREA_NAME
    &returnGeometry=true
    &outSR=4326
    &f=geojson
  ```

- __PostGIS: spatial join incidents → neighbourhoods (robust)__
  ```sql
  -- assumes SRID 4326 for both tables
  SELECT n.area_long_code, n.area_name, COUNT(i.*) AS cnt
  FROM cot_neighbourhoods_158 n
  LEFT JOIN tps_incidents i
    ON ST_Intersects(n.geom, i.geom)
    AND i.report_date >= DATE '2024-01-01'
    AND i.report_date <  DATE '2025-01-01'
  GROUP BY n.area_long_code, n.area_name
  ORDER BY n.area_long_code;
  ```

- __PostGIS: code-based join (if HOOD_158 aligns with area codes)__
  ```sql
  SELECT n.area_long_code, n.area_name, c.cnt
  FROM cot_neighbourhoods_158 n
  LEFT JOIN (
    SELECT hood_158::text AS area_long_code, COUNT(*) AS cnt
    FROM tps_incidents
    WHERE report_date >= DATE '2024-01-01' AND report_date < DATE '2025-01-01'
    GROUP BY hood_158
  ) c USING (area_long_code)
  ORDER BY n.area_long_code;
  ```

## ETL Mirroring Plan (PostGIS)

- __Targets__
  - `tps_incidents` (Point, SRID 4326) — union of Robbery, Theft Over, B&E (retain source in `dataset` column).
  - `cot_neighbourhoods_158` (Polygon, SRID 4326) — from City FeatureServer.

- __Schema (minimal)__
  ```sql
  -- neighbourhoods
  CREATE TABLE IF NOT EXISTS cot_neighbourhoods_158 (
    area_long_code text PRIMARY KEY,
    area_short_code text,
    area_name text,
    geom geometry(Polygon, 4326)
  );
  CREATE INDEX IF NOT EXISTS idx_cot_n158_geom ON cot_neighbourhoods_158 USING gist (geom);

  -- incidents (unioned)
  CREATE TABLE IF NOT EXISTS tps_incidents (
    id bigserial PRIMARY KEY,
    dataset text NOT NULL, -- robbery | theft_over | break_and_enter
    event_unique_id text,
    report_date timestamptz,
    occ_date timestamptz,
    offence text,
    mci_category text,
    hood_158 text,
    lon double precision,
    lat double precision,
    geom geometry(Point, 4326)
  );
  CREATE INDEX IF NOT EXISTS idx_tps_incidents_geom ON tps_incidents USING gist (geom);
  CREATE INDEX IF NOT EXISTS idx_tps_incidents_report_date ON tps_incidents (report_date);
  ```

- __Ingest (examples)__
  - Neighbourhoods via FeatureServer → GeoJSON → ogr2ogr:
    ```bash
    ogr2ogr -f PostgreSQL PG:"$PG_DSN" \
      "https://services3.arcgis.com/b9WvedVPoizGfvfD/arcgis/rest/services/COTGEO_CENSUS_NEIGHBORHOOD/FeatureServer/0/query?where=1%3D1&outFields=AREA_LONG_CODE,AREA_SHORT_CODE,AREA_NAME&returnGeometry=true&outSR=4326&f=geojson" \
      -nln cot_neighbourhoods_158 -nlt PROMOTE_TO_MULTI -overwrite
    ```
  - Incidents: pull each TPS layer, map fields, upsert into `tps_incidents` (pseudo):
    ```bash
    # Example for Robbery
    curl -s "https://services.arcgis.com/S9th0jAJ7bqgIRjw/arcgis/rest/services/Robbery_Open_Data/FeatureServer/0/query?where=1%3D1&outFields=EVENT_UNIQUE_ID,REPORT_DATE,OCC_DATE,OFFENCE,MCI_CATEGORY,HOOD_158,LONG_WGS84,LAT_WGS84&f=json" | \
      node transform_to_copy.js robbery | psql "$PG_DSN" -c "\copy tps_incidents(dataset,event_unique_id,report_date,occ_date,offence,mci_category,hood_158,lon,lat,geom) FROM STDIN WITH (FORMAT csv)" 
    ```

- __Refresh cadence__
  - Neighbourhoods: rarely changes; refresh monthly or on schema notice.
  - Incidents: refresh daily; use `resultOffset`/`where=REPORT_DATE >= CURRENT_DATE - INTERVAL '2 days'` for incremental loads.

- __Caching & performance__
  - Enable HTTP caching for ArcGIS reads; mirror to PostGIS for API speed.
  - Precompute daily aggregates by neighbourhood into a materialized view.

## Backend API (proposed, minimal)

- __GET /api/incidents__ — proxied ArcGIS or PostGIS-backed with filters: bbox, from, to, category.
- __GET /api/neighbourhoods__ — polygons with minimal fields for map.
- __GET /api/choropleth__ — counts per neighbourhood (date range, category), returns GeoJSON or JSON + codes.
