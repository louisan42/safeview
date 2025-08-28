import os
import json
import yaml
from pathlib import Path
from datetime import datetime, timedelta, timezone
from time import perf_counter

from etl.db import connect, ensure_tables, copy_incidents_csv, post_load_cleanup, upsert_neighbourhoods
from etl.transform import fetch_paginated, build_incidents_csv, fetch_neighbourhoods_geojson

FIELDS = 'EVENT_UNIQUE_ID,REPORT_DATE,OCC_DATE,OFFENCE,MCI_CATEGORY,HOOD_158,LONG_WGS84,LAT_WGS84'

def load_config() -> dict:
    # Allow ETL_CONFIG env var, else default to etl/config.yaml next to this file
    cfg_path = os.getenv('ETL_CONFIG') or str(Path(__file__).with_name('config.yaml'))
    if not os.path.exists(cfg_path):
        raise FileNotFoundError(f"Config not found: {cfg_path}. Copy etl/config.example.yaml to etl/config.yaml and edit.")
    with open(cfg_path, 'r') as f:
        cfg = yaml.safe_load(f)
    # Env overrides for CI
    etl_env = cfg.get('etl', {}) or {}
    if os.getenv('ETL_WINDOW_DAYS'):
        try:
            etl_env['incidents_window_days'] = int(os.getenv('ETL_WINDOW_DAYS'))
        except ValueError:
            pass
    if os.getenv('ETL_BACKFILL'):
        etl_env['backfill'] = os.getenv('ETL_BACKFILL', '').lower() in ('1', 'true', 'yes', 'on')
    if os.getenv('ETL_BACKFILL_START'):
        etl_env['backfill_start'] = os.getenv('ETL_BACKFILL_START')
    cfg['etl'] = etl_env
    return cfg


def _epoch_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def incidents_where(window_days: int, etl_cfg: dict) -> str:
    # Backfill mode supports full table or from a given start date
    if bool(etl_cfg.get('backfill', False)):
        start = etl_cfg.get('backfill_start')
        if start:
            # Expect YYYY-MM-DD; assume 00:00:00Z
            dt = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
            return f"REPORT_DATE >= {_epoch_ms(dt)}"
        return "1=1"
    # Regular incremental: epoch-ms cutoff
    cutoff = datetime.now(timezone.utc) - timedelta(days=int(window_days))
    return f"REPORT_DATE >= {_epoch_ms(cutoff)}"


def run():
    cfg = load_config()
    # Allow PG_DSN env override
    pg_dsn = os.getenv('PG_DSN') or cfg['pg_dsn']
    services = cfg['services']
    nbhd_cfg = cfg.get('neighbourhoods', {})
    etl = cfg.get('etl', {})
    window_days = int(etl.get('incidents_window_days', 7))
    batch_size = int(etl.get('batch_size', 2000))
    max_retries = int(etl.get('max_retries', 4))
    backoff = int(etl.get('retry_backoff_seconds', 2))

    where = incidents_where(window_days, etl)

    conn = connect(pg_dsn)
    totals = {"inserted": 0, "datasets": {}}
    try:
        ensure_tables(conn)
        # Incidents
        for dataset, url in services.items():
            print(f"[ETL] Fetching {dataset} from {url}")
            print(f"[ETL] Using WHERE: {where}")
            t0 = perf_counter()
            rows = fetch_paginated(
                service_url=url,
                where=where,
                fields=FIELDS,
                batch_size=batch_size,
                max_retries=max_retries,
                backoff=backoff,
            )
            buf = build_incidents_csv(dataset, rows)
            text = buf.getvalue()
            if text == '':
                print(f"[ETL] No rows for {dataset} (window_days={window_days}, backfill={bool(etl.get('backfill', False))}).")
                continue
            row_count = text.count('\n') if text else 0
            copy_incidents_csv(conn, buf)
            post_load_cleanup(conn)
            dur = perf_counter() - t0
            totals["datasets"][dataset] = {"rows": row_count, "seconds": round(dur, 2)}
            totals["inserted"] += row_count
            print(f"[ETL] Upserted {dataset}: rows={row_count}, time={dur:.2f}s.")

        # Neighbourhood polygons
        if nbhd_cfg:
            nbhd_url = nbhd_cfg['url']
            nbhd_fields = nbhd_cfg.get('fields', 'AREA_LONG_CODE,AREA_SHORT_CODE,AREA_NAME')
            print(f"[ETL] Fetching neighbourhoods from {nbhd_url}")
            t0 = perf_counter()
            features = fetch_neighbourhoods_geojson(nbhd_url, nbhd_fields, max_retries, backoff)
            rows = []
            for f in features:
                props = f.get('properties', {})
                geom = f.get('geometry')
                if not geom:
                    continue
                rows.append(
                    (
                        str(props.get('AREA_LONG_CODE', '')),
                        str(props.get('AREA_SHORT_CODE', '')),
                        str(props.get('AREA_NAME', '')),
                        json.dumps(geom),
                    )
                )
            if rows:
                upsert_neighbourhoods(conn, rows)
                dur = perf_counter() - t0
                print(f"[ETL] Upserted neighbourhoods: rows={len(rows)}, time={dur:.2f}s.")
            else:
                print("[ETL] No neighbourhood features returned.")

        # Summary
        print("[ETL] Summary:")
        for ds, m in totals["datasets"].items():
            print(f"  - {ds}: rows={m['rows']}, time={m['seconds']}s")
        print(f"  Total incident rows processed: {totals['inserted']}")
    finally:
        conn.close()


if __name__ == '__main__':
    run()
