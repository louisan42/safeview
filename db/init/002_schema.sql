-- Minimal schema for integration tests

-- Neighbourhoods table
CREATE TABLE IF NOT EXISTS cot_neighbourhoods_158 (
  area_long_code text PRIMARY KEY,
  area_short_code text,
  area_name text,
  geom geometry(Polygon, 4326)
);

-- Incidents table
CREATE TABLE IF NOT EXISTS tps_incidents (
  id serial PRIMARY KEY,
  dataset text,
  event_unique_id text,
  report_date timestamp with time zone,
  occ_date timestamp with time zone,
  offence text,
  mci_category text,
  hood_158 text,
  lon double precision,
  lat double precision,
  geom geometry(Point, 4326)
);

CREATE INDEX IF NOT EXISTS idx_tps_incidents_geom ON tps_incidents USING gist (geom);
CREATE INDEX IF NOT EXISTS idx_cot_neighbourhoods_geom ON cot_neighbourhoods_158 USING gist (geom);
