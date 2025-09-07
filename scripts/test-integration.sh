#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Starting integration test database...${NC}"

# Start test database
docker-compose -f docker-compose.test.yml up -d test-db

# Wait for database to be ready
echo -e "${YELLOW}⏳ Waiting for database to be ready...${NC}"
until docker-compose -f docker-compose.test.yml exec -T test-db pg_isready -U sv_test -d sv_test; do
  echo "Waiting for database..."
  sleep 2
done

echo -e "${GREEN}✅ Database is ready!${NC}"

# Set environment variable and run integration tests
export PG_DSN="postgresql://sv_test:sv_test@localhost:55433/sv_test"

echo -e "${YELLOW}🧪 Running integration tests...${NC}"
pytest -m integration api/tests -v

# Cleanup
echo -e "${YELLOW}🧹 Cleaning up...${NC}"
docker-compose -f docker-compose.test.yml down

echo -e "${GREEN}✅ Integration tests complete!${NC}"
