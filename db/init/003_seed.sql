-- Seed minimal data for integration tests

-- Insert a square neighbourhood polygon roughly around Toronto coordinates
INSERT INTO cot_neighbourhoods_158 (area_long_code, area_short_code, area_name, geom)
VALUES (
  '001', '1', 'Test Region',
  ST_SetSRID(
    ST_GeomFromText('POLYGON((-79.6 43.6, -79.3 43.6, -79.3 43.8, -79.6 43.8, -79.6 43.6))'),
    4326
  )
) ON CONFLICT (area_long_code) DO NOTHING;

-- Insert a point incident inside that polygon
INSERT INTO tps_incidents (
  dataset, event_unique_id, report_date, occ_date, offence, mci_category, hood_158, lon, lat, geom
) VALUES (
  'robbery', 'E1', '2025-01-01T00:00:00Z', '2025-01-01T00:00:00Z', 'Robbery', 'Robbery', '001', -79.4, 43.7,
  ST_SetSRID(ST_MakePoint(-79.4, 43.7), 4326)
);
