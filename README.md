# SafetyView ETL

A small ETL that ingests Toronto Police Service incidents and City of Toronto neighbourhood polygons into PostgreSQL/PostGIS.

## Structure
- `etl/main.py` – entrypoint
- `etl/transform.py` – HTTP fetch + transform to CSV
- `etl/db.py` – schema, copy/upsert, post-load cleanup
- `etl/config.example.yaml` – template for local config (do NOT commit secrets)
- `.github/workflows/etl.yml` – CI to run nightly and on changes

## Local Setup
1. Python 3.13 (recommended)
2. Create venv and install deps:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r etl/requirements.txt
   ```
3. Create config from template and fill DSN:
   ```bash
   cp etl/config.example.yaml etl/config.yaml
   # edit etl/config.yaml: set pg_dsn
   ```
4. Run:
   ```bash
   python -m etl.main
   # or with env overrides
   PG_DSN=postgresql://user:pass@host:5432/db \
   ETL_WINDOW_DAYS=7 ETL_BACKFILL=false \
   python -m etl.main
   ```

## Backfill
- Full table: set `ETL_BACKFILL=true` (or `etl.backfill: true` in config)
- From date: `ETL_BACKFILL=true ETL_BACKFILL_START=YYYY-MM-DD`

## CI (GitHub Actions)
- Workflow: `.github/workflows/etl.yml`
- Triggers: nightly (05:30 UTC), on `etl/**` changes, and manual dispatch
- Secrets:
  - `PG_DSN` – your Postgres connection string (e.g., Supabase direct connection)
- Manual run: GitHub → Actions → ETL → Run workflow (optionally set window/backfill inputs)

## Notes
- Do NOT commit secrets. `etl/config.yaml` is ignored via `.gitignore`. Use `etl/config.example.yaml` for templates.
- PostGIS must be enabled in the target DB (on Supabase: `create extension if not exists postgis;`).
- Loads are idempotent: staging + dedup + upsert avoids unique violations; geometry and cleanup performed post-load.
