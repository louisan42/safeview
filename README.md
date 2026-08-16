# Watchtile

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=louisan42_safeview&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=louisan42_safeview)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=louisan42_safeview&metric=coverage)](https://sonarcloud.io/summary/new_code?id=louisan42_safeview)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=louisan42_safeview&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=louisan42_safeview)

Watchtile (full name: Neighbourhood Watchtile) is a civic crime and safety map for Toronto. The product name is **Watchtile**; this repository and GitHub project remain **SafetyView** (`louisan42/safeview`).

Production (Railway):
- Web: https://web-production-69f87.up.railway.app
- API: https://api-production-2c307.up.railway.app
- Health: https://api-production-2c307.up.railway.app/health

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

`main` is protected: changes go through a pull request. Direct pushes to `main` are blocked for everyone except a repository admin who explicitly bypasses protection.

1. Open a PR against `main`.
2. **CI** runs (API unit tests, PostGIS integration tests, web production build). The PR cannot merge while CI is red.
3. Railway creates an isolated **PR environment** from the `staging` base (own API, web, and PostGIS — not production data). Sign-in uses the Clerk **development** instance.
4. Railway comments the preview URLs on the PR. Long-lived staging is `https://web-staging-81f9.up.railway.app` / `https://api-staging-5b49.up.railway.app`. PR hosts look like `https://<service>-pr-<number>-<hash>.up.railway.app` (exact hosts are in the Railway comment).
5. Merge the PR. Railway deletes the PR environment.
6. A push to `main` deploys **production** only after CI is green (**Wait for CI**). A failed CI run skips the production deploy.
7. `Production health check` then curls the live API `/health` and the web origin. It does not deploy.

There is no Coolify path. Do not use `railway up` as the happy path — that is CLI-only emergency recovery if GitHub autodeploy is broken.

### Branch protection

Required status checks on `main`: **API unit tests**, **API integration tests**, **Web build**. Conversation resolution is required. Repository admins can still bypass GitHub rules; everyone else must use a PR.

### Railway environments

| Environment | Git trigger | Database | Clerk |
| --- | --- | --- | --- |
| production | `main` after CI | production PostGIS | leave `VITE_CLERK_PUBLISHABLE_KEY` unset to keep the map public, or set `pk_live_` when you turn on production auth |
| staging | PR-environment base (not a second production) | isolated PostGIS | Clerk **development** `pk_test_` |
| PR / preview | each open PR | clone of staging PostGIS (empty, isolated) | inherits staging development keys |

Project: https://railway.com/project/fb2ac2a8-5df1-4355-8979-7d484cb1db8e

GitHub Actions does not need a Railway API token. Railway's GitHub integration deploys from `louisan42/safeview`.

One-time Railway dashboard clicks (not available via CLI/API):

1. **Wait for CI** — each of **api** and **web** in **production** → Settings → Source / Deploy → enable **Wait for CI**. Failed GitHub **CI** then `SKIPPED` the production deploy.
2. **PR environments** — Project Settings → Environments → **Enable PR Environments** → base environment **staging** (not production). Leave Bot PR Environments off.

### Clerk

Vite React uses `@clerk/react` and `VITE_CLERK_PUBLISHABLE_KEY` (baked in at Docker build time). Secret keys stay out of git.

- Staging / PR: Clerk application **Watchtile Staging**, development instance.
- Production: Clerk production keys on the Railway production web service only when you want auth on the public map.
- Local: copy `env.example` to `.env` and optionally set a `pk_test_` key. With no key, the map stays public.

The Clerk application **Watchtile Staging** (`app_3I1FJydfYsfQB48So0znHL5sLwj`) already exists. Dashboard leftovers:

1. [Clerk Dashboard](https://dashboard.clerk.com) → **Watchtile Staging** → **Configure** → **Domains**.
2. Add `https://web-staging-81f9.up.railway.app` and each PR web origin Railway comments (or `https://*.up.railway.app` if the UI allows a wildcard).
3. Development instance → [API keys](https://dashboard.clerk.com/~/api-keys): publishable key is already set on the Railway **staging** web service as `VITE_CLERK_PUBLISHABLE_KEY`. Do not paste secret keys into git.

### Services

| Service | Dockerfile | Config | Port |
| --- | --- | --- | --- |
| api | `Dockerfile.api` | `railway.toml` | **8888** (`/health`) |
| web | `Dockerfile.web` | `railway.web.toml` | **80** (nginx; `/api` proxied to the API) |
| Postgres | Railway plugin | PostGIS enabled | private + public TCP |

Web build uses `VITE_API_BASE_URL=/api`. At runtime set `API_UPSTREAM` on the web service to `${{api.RAILWAY_PRIVATE_DOMAIN}}:${{api.PORT}}`. Set `CORS_ORIGINS` on the API to include the production and staging web origins. Never log `PG_DSN` or `DATABASE_URL`. Staging DB URL must not be the production DSN.

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
- `deploy.sh` is local Docker only; production is Railway from `main` via GitHub.
