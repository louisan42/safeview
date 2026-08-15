# Lotline

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=louisan42_safeview&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=louisan42_safeview)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=louisan42_safeview&metric=coverage)](https://sonarcloud.io/summary/new_code?id=louisan42_safeview)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=louisan42_safeview&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=louisan42_safeview)

Lotline is a civic crime and safety map for Toronto. The product name is **Lotline**; this repository and GitHub project remain **SafetyView** (`louisan42/safeview`).

Production (Railway):
- Web: https://web-production-69f87.up.railway.app
- API: https://api-production-2c307.up.railway.app
- Health: https://api-production-2c307.up.railway.app/health

## Overview

- **ETL** (`etl/`) — weekly ingest of Toronto Police Service open data (robbery, theft over, break and enter)
- **API** (`api/`) — FastAPI with PostGIS-backed incidents, neighbourhoods, and analytics
- **Web** (`web/`) — React + Leaflet map (Lotline UI)
- **Database** — PostgreSQL / PostGIS (local Docker or Railway)

## Local quick start

Prerequisites: Docker, Python 3.11+, Node.js 18+.

```bash
git clone https://github.com/louisan42/safeview.git
cd SafetyView
cp env.example .env
```

### Docker (database + API + web)

```bash
./deploy.sh
# or: docker compose -f docker-compose.dev.yml up -d
```

- Frontend: http://localhost:5173
- API: http://localhost:8888
- API docs: http://localhost:8888/docs
- Database: localhost:55432

### Manual

```bash
docker compose -f docker-compose.dev.yml up -d db

# API
python -m venv .venv
source .venv/bin/activate
pip install -r api/requirements.txt
export PG_DSN="postgresql://sv:sv@localhost:55432/sv"
python -m api.main          # http://localhost:8888

# Web
cd web
npm install
npm run dev                 # http://localhost:5173
```

### ETL (optional)

```bash
cp etl/config.example.yaml etl/config.yaml
# set pg_dsn — never commit config.yaml
pip install -r etl/requirements.txt
python -m etl.main
```

The weekly GitHub Action uses `PG_DSN` (Railway public TCP) with secret masking. Default window is 90 days.

## Deploy (Railway)

Railway is connected to `louisan42/safeview` and **auto-deploys API and web on push to `main`**. There is no Coolify webhook and no Railway token in this repo.

| Service | Dockerfile | Config | Port |
| --- | --- | --- | --- |
| api | `Dockerfile.api` | `railway.toml` | **8888** (`/health`) |
| web | `Dockerfile.web` | `railway.web.toml` | **80** (nginx; `/api` proxied to the API) |
| Postgres | Railway plugin | PostGIS enabled | private + public TCP |

CI (`CI` workflow) runs on every pull request and on `main`. After CI succeeds on `main`, `Production health check` curls the live API `/health` and the web origin.

Recommended Railway setting: enable **Wait for CI** on the api and web services so a failing test run skips the deploy.

Web build uses `VITE_API_BASE_URL=/api`. At runtime set `API_UPSTREAM` on the web service to `${{api.RAILWAY_PRIVATE_DOMAIN}}:${{api.PORT}}`. Set `CORS_ORIGINS` on the API to include `https://web-production-69f87.up.railway.app`.

## Testing

```bash
make test                 # unit tests (mocked DB)
make test-integration     # PostGIS integration tests
make test-coverage
```

GitHub Actions runs unit tests, PostGIS integration tests, and a web production build.

## Notes

- Product name: Lotline. Repo / package names: SafetyView, `louisan42/safeview`.
- API port is **8888** everywhere (local, Docker, Railway). Do not use 8000.
- Never commit secrets. `etl/config.yaml` is gitignored. Do not log `PG_DSN`.
- `deploy.sh` is local Docker only; production is Railway from `main`.
