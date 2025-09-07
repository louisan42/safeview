#!/bin/bash

# SafetyView Deployment Script for Coolify
# Usage: ./deploy.sh [environment]
# Environment: dev (default) or prod

set -e

ENVIRONMENT=${1:-dev}
COMPOSE_FILE="docker-compose.dev.yml"

if [ "$ENVIRONMENT" = "prod" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
# CI environment no longer needs compose file - uses in-memory tests
fi

echo "🚀 Deploying SafetyView ($ENVIRONMENT environment)..."

# Check if required files exist
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ Error: $COMPOSE_FILE not found!"
    exit 1
fi

# Load environment variables if .env exists
if [ -f ".env" ]; then
    echo "📄 Loading environment variables from .env"
    export $(cat .env | grep -v '^#' | xargs)
fi

# Build and deploy
echo "🔨 Building and starting services..."
docker-compose -f "$COMPOSE_FILE" down --remove-orphans
docker-compose -f "$COMPOSE_FILE" build --no-cache
docker-compose -f "$COMPOSE_FILE" up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check health
echo "🏥 Checking service health..."
if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up (healthy)"; then
    echo "✅ Services are healthy!"
else
    echo "⚠️  Some services may not be fully ready yet. Check logs:"
    echo "   docker-compose -f $COMPOSE_FILE logs"
fi

# Show status
echo "📊 Service status:"
docker-compose -f "$COMPOSE_FILE" ps

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📱 Frontend: http://localhost"
echo "🔌 API: http://localhost:8000"
echo "🗄️  Database: localhost:${PG_PORT:-55432}"
echo ""
echo "📋 Useful commands:"
echo "   View logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "   Stop: docker-compose -f $COMPOSE_FILE down"
echo "   Restart: docker-compose -f $COMPOSE_FILE restart"
