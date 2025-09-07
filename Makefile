.PHONY: test test-unit test-integration test-coverage test-db-up test-db-down help

# Default target
help:
	@echo "SafetyView Testing Commands:"
	@echo "  make test           - Run all unit tests (fast, no DB required)"
	@echo "  make test-unit      - Run unit tests only"
	@echo "  make test-integration - Run integration tests with live PostGIS"
	@echo "  make test-coverage  - Run tests with HTML coverage report"
	@echo "  make test-db-up     - Start test database only"
	@echo "  make test-db-down   - Stop test database"

# Fast unit tests (default)
test:
	pytest -m "not integration"

# Unit tests explicitly
test-unit:
	pytest -m "not integration" -v

# Integration tests with live database
test-integration:
	@echo "🚀 Starting integration tests with live PostGIS..."
	docker-compose -f docker-compose.test.yml up -d test-db
	@echo "⏳ Waiting for database..."
	@until docker-compose -f docker-compose.test.yml exec -T test-db pg_isready -U sv_test -d sv_test >/dev/null 2>&1; do sleep 1; done
	@echo "✅ Database ready!"
	PG_DSN="postgresql://sv_test:sv_test@localhost:55433/sv_test" pytest -m integration api/tests -v
	@echo "🧹 Cleaning up..."
	docker-compose -f docker-compose.test.yml down

# Coverage report
test-coverage:
	pytest --cov=api --cov-report=html --cov-report=term-missing
	@echo "📊 Coverage report: open htmlcov/index.html"

# Database management
test-db-up:
	docker-compose -f docker-compose.test.yml up -d test-db
	@echo "⏳ Waiting for database..."
	@until docker-compose -f docker-compose.test.yml exec -T test-db pg_isready -U sv_test -d sv_test >/dev/null 2>&1; do sleep 1; done
	@echo "✅ Test database ready at postgresql://sv_test:sv_test@localhost:55433/sv_test"

test-db-down:
	docker-compose -f docker-compose.test.yml down
