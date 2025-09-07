import psycopg
from typing import List, Tuple

DDL_ENABLE_POSTGIS = """
CREATE EXTENSION IF NOT EXISTS postgis;
"""

DDL_METADATA = """
CREATE TABLE IF NOT EXISTS etl_metadata (
  key text PRIMARY KEY,
  value text
);
"""

DDL_NEIGHBOURHOODS = """
CREATE TABLE IF NOT EXISTS cot_neighbourhoods_158 (
  area_long_code text PRIMARY KEY,
  area_short_code text,
  area_name text,
  geom geometry(Polygon, 4326)
);
CREATE INDEX IF NOT EXISTS idx_cot_n158_geom ON cot_neighbourhoods_158 USING gist (geom);
"""

DDL_INCIDENTS = """
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
CREATE UNIQUE INDEX IF NOT EXISTS ux_tps_incidents_dataset_euid ON tps_incidents (dataset, event_unique_id);
"""

DDL_ANALYTICS_VIEWS = """
CREATE OR REPLACE VIEW v_incidents_daily with (security_barrier = 'on') AS
SELECT
  date_trunc('day', report_date) AS day,
  dataset,
  COUNT(*) AS cnt
FROM tps_incidents
WHERE report_date IS NOT NULL
GROUP BY 1,2;

CREATE OR REPLACE VIEW v_incidents_by_neighbourhood with (security_barrier = 'on') AS
SELECT
  dataset,
  hood_158,
  COUNT(*) AS cnt
FROM tps_incidents
GROUP BY 1,2;

CREATE OR REPLACE VIEW v_incidents_last_30d with (security_barrier = 'on') AS
SELECT *
FROM tps_incidents
WHERE report_date >= now() - interval '30 days';
"""

POST_LOAD_SQL = """
-- set geom for rows lacking geometry
UPDATE tps_incidents SET geom = ST_SetSRID(ST_MakePoint(lon,lat),4326) WHERE geom IS NULL AND lon IS NOT NULL AND lat IS NOT NULL;
-- remove duplicates by (dataset,event_unique_id)
DELETE FROM tps_incidents t
USING (
  SELECT dataset,event_unique_id, ctid, ROW_NUMBER() OVER (PARTITION BY dataset,event_unique_id ORDER BY ctid) AS rn
  FROM tps_incidents
) d
WHERE t.ctid = d.ctid AND d.rn > 1;
"""

def connect(pg_dsn: str):
    return psycopg.connect(pg_dsn, options='-c idle_in_transaction_session_timeout=0')


def ensure_tables(conn):
    with conn.cursor() as cur:
        # On managed providers (e.g., Supabase), CREATE EXTENSION may require elevated privileges.
        # Try to enable PostGIS, but continue if not permitted assuming it is already installed.
        try:
            cur.execute(DDL_ENABLE_POSTGIS)
        except Exception as e:
            print(f"[ETL][warn] Skipping CREATE EXTENSION postgis (permission or already installed): {e}")
        cur.execute(DDL_NEIGHBOURHOODS)
        cur.execute(DDL_INCIDENTS)
        cur.execute(DDL_METADATA)
        # Create/refresh analytics views
        try:
            cur.execute(DDL_ANALYTICS_VIEWS)
        except Exception as e:
            print(f"[ETL][warn] Skipping analytics views creation: {e}")
    conn.commit()


def copy_incidents_csv(conn, csv_buffer):
    """
    Load CSV into a temporary staging table, then upsert into tps_incidents.
    This avoids unique violations when reprocessing/backfilling.
    """
    with conn.cursor() as cur:
        # Temp table matches COPY columns (no id/geom)
        cur.execute(
            """
            CREATE TEMP TABLE tps_incidents_stage (
              dataset text,
              event_unique_id text,
              report_date timestamptz,
              occ_date timestamptz,
              offence text,
              mci_category text,
              hood_158 text,
              lon double precision,
              lat double precision
            ) ON COMMIT DROP
            """
        )
        # COPY into stage
        with cur.copy(
            """
            COPY tps_incidents_stage(dataset,event_unique_id,report_date,occ_date,offence,mci_category,hood_158,lon,lat)
            FROM STDIN WITH (FORMAT csv, NULL '')
            """
        ) as copy:
            copy.write(csv_buffer.getvalue())
        # Upsert from a deduplicated view of staging to avoid ON CONFLICT touching same row twice
        cur.execute(
            """
            WITH dedup AS (
              SELECT DISTINCT ON (dataset, event_unique_id)
                dataset, event_unique_id, report_date, occ_date, offence, mci_category, hood_158, lon, lat
              FROM tps_incidents_stage
              ORDER BY dataset, event_unique_id, report_date DESC NULLS LAST, occ_date DESC NULLS LAST
            )
            INSERT INTO tps_incidents(dataset,event_unique_id,report_date,occ_date,offence,mci_category,hood_158,lon,lat)
            SELECT dataset,event_unique_id,report_date,occ_date,offence,mci_category,hood_158,lon,lat
            FROM dedup
            ON CONFLICT (dataset, event_unique_id) DO UPDATE SET
              report_date = EXCLUDED.report_date,
              occ_date = EXCLUDED.occ_date,
              offence = EXCLUDED.offence,
              mci_category = EXCLUDED.mci_category,
              hood_158 = EXCLUDED.hood_158,
              lon = EXCLUDED.lon,
              lat = EXCLUDED.lat
            """
        )
    conn.commit()


def post_load_cleanup(conn):
    with conn.cursor() as cur:
        cur.execute(POST_LOAD_SQL)
    conn.commit()


def upsert_neighbourhoods(conn, rows: List[Tuple[str, str, str, str]]):
    """
    Insert/update neighbourhood polygons.
    rows: list of (area_long_code, area_short_code, area_name, geom_geojson)
    """
    sql = (
        """
        INSERT INTO cot_neighbourhoods_158(area_long_code, area_short_code, area_name, geom)
        VALUES (%s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
        ON CONFLICT (area_long_code) DO UPDATE SET
          area_short_code = EXCLUDED.area_short_code,
          area_name = EXCLUDED.area_name,
          geom = EXCLUDED.geom
        """
    )
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    conn.commit()


def set_metadata(conn, key: str, value: str):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO etl_metadata(key, value)
            VALUES (%s, %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
            """,
            (key, value),
        )
    conn.commit()
