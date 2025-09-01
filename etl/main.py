import os
import json
import yaml
from pathlib import Path
from datetime import datetime, timedelta, timezone
from time import perf_counter
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from etl.db import connect, ensure_tables, copy_incidents_csv, post_load_cleanup, upsert_neighbourhoods
from etl.transform import fetch_paginated, build_incidents_csv, fetch_neighbourhoods_geojson

FIELDS = 'EVENT_UNIQUE_ID,REPORT_DATE,OCC_DATE,OFFENCE,MCI_CATEGORY,HOOD_158,LONG_WGS84,LAT_WGS84'

def load_config() -> dict:
    # Prefer ETL_CONFIG, else try etl/config.yaml next to this file
    cfg_path = os.getenv('ETL_CONFIG') or str(Path(__file__).with_name('config.yaml'))
    cfg: dict | None = None
    if os.path.exists(cfg_path):
        with open(cfg_path, 'r') as f:
            cfg = yaml.safe_load(f)
    else:
        # Try example config if present
        example_path = Path(__file__).with_name('config.example.yaml')
        if example_path.exists():
            with open(example_path, 'r') as f:
                cfg = yaml.safe_load(f)
        else:
            cfg = None
    # If no file available, build minimal defaults requiring PG_DSN
    if cfg is None:
        pg_dsn_env = os.getenv('PG_DSN')
        if not pg_dsn_env:
            raise FileNotFoundError(
                f"Config not found: {cfg_path}. Set PG_DSN env or add etl/config.yaml (see etl/config.example.yaml)."
            )
        cfg = {
            'pg_dsn': pg_dsn_env,
            'services': {
                'robbery': 'https://services.arcgis.com/S9th0jAJ7bqgIRjw/arcgis/rest/services/Robbery_Open_Data/FeatureServer/0/query',
                'theft_over': 'https://services.arcgis.com/S9th0jAJ7bqgIRjw/arcgis/rest/services/Theft_Over_Open_Data/FeatureServer/0/query',
                'break_and_enter': 'https://services.arcgis.com/S9th0jAJ7bqgIRjw/arcgis/rest/services/Break_and_Enter_Open_Data/FeatureServer/0/query',
            },
            'neighbourhoods': {
                'url': 'https://services3.arcgis.com/b9WvedVPoizGfvfD/arcgis/rest/services/COTGEO_CENSUS_NEIGHBORHOOD/FeatureServer/0/query',
                'fields': 'AREA_LONG_CODE,AREA_SHORT_CODE,AREA_NAME',
            },
            'etl': {
                'incidents_window_days': 7,
                'batch_size': 2000,
                'max_retries': 4,
                'retry_backoff_seconds': 2,
                'backfill': False,
            },
        }
    # Ensure pg_dsn present; allow PG_DSN env to override
    if os.getenv('PG_DSN'):
        cfg['pg_dsn'] = os.getenv('PG_DSN')
    if 'pg_dsn' not in cfg or not cfg['pg_dsn']:
        raise FileNotFoundError("pg_dsn missing. Provide PG_DSN env or set in config.yaml.")

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
    # Diagnostics: parse DSN to log host/port/dbname/sslmode without secrets
    def _redact_dsn_info(dsn: str) -> dict:
        try:
            u = urlparse(dsn)
            q = parse_qs(u.query)
            return {
                'scheme': u.scheme,
                'host': u.hostname,
                'port': u.port,
                'dbname': (u.path.lstrip('/') if u.path else None),
                'sslmode': (q.get('sslmode', [''])[0] or None),
            }
        except Exception:
            return {'scheme': None, 'host': None, 'port': None, 'dbname': None, 'sslmode': None}

    info = _redact_dsn_info(pg_dsn)
    print(f"[ETL] DB target host={info.get('host')} port={info.get('port')} db={info.get('dbname')} sslmode={info.get('sslmode')}")

    # In CI, enforce sslmode=require if missing in URL-style DSN
    if os.getenv('GITHUB_ACTIONS', '').lower() == 'true':
        try:
            u = urlparse(pg_dsn)
            if u.scheme and u.hostname:
                q = parse_qs(u.query)
                if 'sslmode' not in q or not q['sslmode']:
                    q['sslmode'] = ['require']
                    new_query = urlencode(q, doseq=True)
                    pg_dsn = urlunparse((u.scheme, u.netloc, u.path, u.params, new_query, u.fragment))
                    print("[ETL] Added sslmode=require for CI connection.")
        except Exception:
            pass
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
                totals["datasets"][dataset] = {"rows": 0, "seconds": 0}
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

        # Data quality checks
        hard_fail = False
        if totals["inserted"] == 0:
            print("[ETL][error] No incident rows processed. Failing the job.")
            hard_fail = True
        else:
            # Warn if any dataset is empty in incremental mode
            empty_ds = [ds for ds, m in totals["datasets"].items() if m["rows"] == 0]
            if empty_ds and not bool(etl.get('backfill', False)):
                print(f"[ETL][warn] Datasets with zero rows this run: {', '.join(empty_ds)}")

        # GitHub Step Summary (if available)
        step_summary = os.getenv('GITHUB_STEP_SUMMARY')
        if step_summary:
            try:
                with open(step_summary, 'a') as f:
                    f.write("\n\n## ETL Summary\n\n")
                    f.write("| Dataset | Rows | Seconds |\n|---|---:|---:|\n")
                    for ds, m in totals["datasets"].items():
                        f.write(f"| {ds} | {m['rows']} | {m['seconds']} |\n")
                    f.write(f"\n**Total incident rows processed:** {totals['inserted']}\n")
            except Exception as e:
                print(f"[ETL][warn] Could not write step summary: {e}")

        if hard_fail:
            raise SystemExit(2)
    finally:
        conn.close()


if __name__ == '__main__':
    run()
