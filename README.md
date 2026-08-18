# Watchtile

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=louisan42_safeview&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=louisan42_safeview)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=louisan42_safeview&metric=coverage)](https://sonarcloud.io/summary/new_code?id=louisan42_safeview)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=louisan42_safeview&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=louisan42_safeview)

Watchtile (full name: Neighbourhood Watchtile) is a civic crime and safety map for Toronto. The product name is **Watchtile**; this repository and GitHub project remain **SafetyView** (`louisan42/safeview`).

Production (Railway, from `main`):
- Web: https://watchtile.koramaple.ca
- API: https://api-production-2c307.up.railway.app
- Health: https://api-production-2c307.up.railway.app/health

Staging (Railway, from `staging`):
- Web: https://web-staging-81f9.up.railway.app
- API: https://api-staging-5b49.up.railway.app
- Health: https://api-staging-5b49.up.railway.app/health

## Overview

- **ETL** (`etl/`) — weekly ingest of Toronto Police Service open data (robbery, theft over, break and enter)
- **API** (`api/`) — FastAPI with PostGIS-backed incidents, neighbourhoods, and analytics
- **Web** (`web/`) — React + Leaflet map (Watchtile UI)
- **Database** — PostgreSQL / PostGIS (local Docker or Railway)

## Local quick start

Prerequisites: Docker, Python 3.11+, Node.js 20+.

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

## How a change ships

The GitHub default branch stays **`main`** (production). Feature PRs must still target **`staging`**. GitHub has no separate “default merge branch” API, so this is enforced with branch rulesets plus a required check on `main`.

```
feature branch
    → PR into staging          (CI: API unit, API integration, web build)
    → merge to staging
    → Railway staging          (https://web-staging-81f9.up.railway.app)
    → PR staging → main        (only allowed promotion into production)
    → merge to main
    → Railway production       (https://watchtile.koramaple.ca)
```

1. Open a feature PR against **`staging`** (`gh pr create --base staging`). Direct PRs into `main` fail the **Require staging → main** check.
2. **CI** runs (API unit tests, PostGIS integration tests, web production build). The PR cannot merge while those checks are red.
3. Merge into `staging`. Railway **staging** deploys from the `staging` branch (long-lived `web-staging-81f9` / `api-staging-5b49`). The map is public; there is no sign-in gate.
4. Open a promotion PR **`staging` → `main`**. That is the only head branch `main` accepts.
5. Merge to `main`. Railway **production** deploys from `main` after CI is green.
6. `Production health check` then curls the live production API `/health` and the web origin. It does not deploy.

There is no Coolify path. Do not use `railway up` from a laptop as the happy path.

### Branch protection

- **`main`**: pull request required, conversation resolution required, no admin bypass, no direct pushes, no force-push. Required checks: **API unit tests**, **API integration tests**, **Web build**, **Require staging → main**.
- **`staging`**: pull request required, conversation resolution required, no admin bypass, no direct pushes, no force-push. Required checks: **API unit tests**, **API integration tests**, **Web build**.

### Railway environments

| Environment | Git trigger | Database |
| --- | --- | --- |
| production | `main` after CI | production PostGIS |
| staging | `staging` branch (not PR Environments, not `cicd/github-railway`) | isolated PostGIS (copy from production via **Refresh staging DB**) |

Project: https://railway.com/project/fb2ac2a8-5df1-4355-8979-7d484cb1db8e

Deploy path: GitHub Actions job **Deploy Railway** (in **CI**) runs `railway up` after tests on push to `staging` or `main`. Secret name only: `RAILWAY_TOKEN` on GitHub Environments **staging** and **production**. The workflow masks it with `::add-mask::`. Never log `RAILWAY_TOKEN`, `PG_DSN`, or `DATABASE_URL`.

If the Railway GitHub App is connected, native Source autodeploy can watch the same branches (**Wait for CI**). Use **either** the Action **or** native autodeploy, not both, or each push deploys twice.

One-time clicks (not available via API):

1. GitHub → Settings → Environments → **production** and **staging** → secret **`RAILWAY_TOKEN`** (Railway project token for that environment).
2. Optional native Source: [install Railway GitHub App](https://github.com/apps/railway-app/installations/new) on `louisan42/safeview`, then each of **api** and **web** → Settings → Source → branch `main` (production) or `staging` (staging) → enable **Wait for CI**. If you do this, disable the **Deploy Railway** CI job so deploys are not doubled.
3. Do **not** enable Railway PR Environments for this promotion flow. Staging is the long-lived `staging` branch.

### Copy production PostGIS → staging

Watchtile has no auth. Staging is for realistic map data, not sign-in. The **Refresh staging DB** workflow (`workflow_dispatch`, reusable via `workflow_call`) dumps production tables with `pg_dump` (custom format) and restores them onto staging PostGIS.

It copies `tps_incidents`, `cot_neighbourhoods_158`, `etl_metadata`, and the analytics views. Weekly **ETL** still writes only to production (`PG_DSN` repo secret). Do not point ETL at staging.

GitHub Environment **staging** secrets (names only — never paste these into issues or logs):

- `PROD_PG_DSN` (or `SOURCE_PG_DSN`) — production **public** TCP URL (`sslmode=require`)
- `STAGING_PG_DSN` — staging **public** TCP URL (`sslmode=prefer` if the proxy does not support SSL)

The staging API `DATABASE_URL` must stay `${{Postgres.DATABASE_URL}}` for the **staging** Postgres plugin. After the workflow exists, run it from Actions → **Refresh staging DB** → Run workflow (this branch or `main` after merge).

The job masks both DSNs (and password/host) with `::add-mask::` before dump/restore, writes the dump to a temp file, deletes it, and uses `set +x`. CI fails if a workflow `echo`s a Postgres URL.

### Services

| Service | Dockerfile | Config | Port |
| --- | --- | --- | --- |
| api | `Dockerfile.api` | `railway.toml` | **8888** (`/health`) |
| web | `Dockerfile.web` | `railway.web.toml` | **80** (nginx; `/api` proxied to the API) |
| Postgres | Railway plugin | PostGIS enabled | private + public TCP |

Web build uses `VITE_API_BASE_URL=/api`. At runtime set `API_UPSTREAM` on the web service to `${{api.RAILWAY_PRIVATE_DOMAIN}}:${{api.PORT}}`. Set `CORS_ORIGINS` on the production API to include `https://watchtile.koramaple.ca` (and local Vite `http://localhost:5173`). Staging API CORS should include `https://web-staging-81f9.up.railway.app`. Never log `PG_DSN` or `DATABASE_URL`. Staging DB URL must not be the production DSN.

## Testing

```bash
make test                 # unit tests (mocked DB)
make test-integration     # PostGIS integration tests
make test-coverage
```

GitHub Actions runs unit tests, PostGIS integration tests, and a web production build.

## Notes

- Product name: Watchtile (Neighbourhood Watchtile). Repo / package names: SafetyView, `louisan42/safeview`.
- API port is **8888** everywhere (local, Docker, Railway). Do not use 8000.
- Never commit secrets. `etl/config.yaml` is gitignored. Do not log `PG_DSN`.
- `deploy.sh` is local Docker only. Staging deploys from `staging`; production deploys from `main`.
