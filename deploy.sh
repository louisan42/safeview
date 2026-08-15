#!/bin/bash
# Local Docker Compose helper for Lotline (SafetyView).
# Production deploys from GitHub → Railway; this script is not used in CI.
# Usage: ./deploy.sh [dev|prod]

set -euo pipefail

ENVIRONMENT=${1:-dev}
COMPOSE_FILE="docker-compose.dev.yml"

if [ "$ENVIRONMENT" = "prod" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
fi

echo "Starting Lotline locally ($ENVIRONMENT) using $COMPOSE_FILE..."

if [ ! -f "$COMPOSE_FILE" ]; then
    echo "Error: $COMPOSE_FILE not found." >&2
    exit 1
fi

if [ -f ".env" ]; then
    echo "Loading environment variables from .env"
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

echo "Building and starting services..."
docker compose -f "$COMPOSE_FILE" down --remove-orphans
docker compose -f "$COMPOSE_FILE" build
docker compose -f "$COMPOSE_FILE" up -d

echo "Waiting for services..."
sleep 10

echo "Service status:"
docker compose -f "$COMPOSE_FILE" ps

echo ""
echo "Local endpoints:"
echo "  Frontend: http://localhost:5173"
echo "  API:      http://localhost:8888"
echo "  API docs: http://localhost:8888/docs"
echo "  Database: localhost:${PG_PORT:-55432}"
echo ""
echo "Production (Railway, auto-deploys from main):"
echo "  https://web-production-69f87.up.railway.app"
echo "  https://api-production-2c307.up.railway.app/health"
echo ""
echo "Logs: docker compose -f $COMPOSE_FILE logs -f"
echo "Stop: docker compose -f $COMPOSE_FILE down"
