# SafetyView

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=louisan42_safeview&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=louisan42_safeview)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=louisan42_safeview&metric=coverage)](https://sonarcloud.io/summary/new_code?id=louisan42_safeview)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=louisan42_safeview&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=louisan42_safeview)

Open-source crime and safety analytics platform with interactive mapping, neighbourhood comparisons, and trend analysis. Built for cities to understand and visualize public safety data.

## 🎯 Project Overview

SafetyView transforms raw crime incident data into actionable insights through:

- **📊 Data Ingestion**: Automated ETL pipeline for Toronto Police Service open data
- **🗺️ Interactive Mapping**: Real-time incident visualization with neighbourhood boundaries
- **📈 Analytics**: Trend analysis, hotspot detection, and per-capita safety metrics
- **🔍 Filtering**: Dynamic filtering by crime type, date range, and geographic area

## 🏗️ Architecture

- **ETL Pipeline** (`etl/`) – Ingests and processes TPS incident data
- **FastAPI Backend** (`api/`) – RESTful API with geospatial endpoints
- **React Frontend** (`web/`) – Interactive map with Tailwind UI
- **PostgreSQL/PostGIS** (`db/`) – Geospatial database for incidents and boundaries
- **Docker** – Containerized development and deployment

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)

### 1. Clone and Setup
```bash
git clone https://github.com/louisan42/safeview.git
cd SafetyView

# Copy environment template
cp env.example .env
# Edit .env with your database configuration
```

### 2. Docker Development (Recommended)
```bash
# Start all services (database, API, frontend)
./deploy.sh

# Or start individual services
docker-compose -f docker-compose.dev.yml up -d db    # Database only
docker-compose -f docker-compose.dev.yml up -d api   # API + Database
docker-compose -f docker-compose.dev.yml up -d       # Full stack
```

**Access Points:**
- 🌐 **Frontend**: http://localhost:3000
- 🔌 **API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs
- 🗄️ **Database**: localhost:55432

### 3. Manual Development Setup

#### Database
```bash
# Start PostgreSQL with PostGIS
docker-compose -f docker-compose.dev.yml up -d db
```

#### Backend API
```bash
cd api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Set database connection
export PG_DSN="postgresql://sv:sv@localhost:55432/sv"

# Start API server
python -m api.main
# API available at http://localhost:8000
```

#### Frontend
```bash
cd web
npm install
npm run dev
# Frontend available at http://localhost:5173
```

#### ETL Pipeline (Optional)
```bash
cd etl
pip install -r requirements.txt

# Configure data source
cp config.example.yaml config.yaml
# Edit config.yaml with your database connection

# Run data ingestion
python -m etl.main
```

## Testing Strategy

SafetyView uses a **two-tier testing approach** for optimal development experience:

### 1. Fast In-Memory Tests (Local Development)
- **Speed**: ~0.7 seconds for full suite
- **Database**: Mocked SQLite in-memory
- **Coverage**: Business logic, API contracts, data transformations
- **Usage**: `pytest` (runs automatically, no setup required)

### 2. Real Database Integration Tests (CI/CD)
- **Speed**: ~10-15 seconds (includes PostGIS setup)
- **Database**: Real PostGIS with test data
- **Coverage**: SQL queries, database constraints, PostGIS functions
- **Usage**: Runs automatically in GitHub Actions

### 🧪 Testing Commands

```bash
# Fast unit tests (recommended for development)
make test                 # or: pytest -m "not integration"

# Integration tests with live PostGIS
make test-integration     # or: pytest -m integration

# Coverage report
make test-coverage        # or: pytest --cov=api --cov-report=html

# All available commands
make help
```

## 📊 Code Quality

This project uses [SonarQube Cloud](https://sonarcloud.io/project/overview?id=louisan42_safeview) for continuous code quality analysis:

- **Quality Gate**: Enforces maintainability, reliability, and security standards
- **Coverage Tracking**: 90% test coverage achieved
- **Code Smells**: Identifies technical debt and improvement opportunities
- **Security Hotspots**: Scans for potential security vulnerabilities

Quality metrics are automatically updated on every push and pull request.

## 🔧 Development Workflow

### Daily Development
```bash
# 1. Start database
docker-compose -f docker-compose.dev.yml up -d db

# 2. Run API in development mode
cd api
source .venv/bin/activate
python -m api.main

# 3. Run frontend in development mode
cd web
npm run dev

# 4. Run tests frequently
make test
```

### API Endpoints
- **Health**: `GET /health`
- **Incidents**: `GET /v1/incidents?dataset=robbery&limit=10`
- **Neighbourhoods**: `GET /v1/neighbourhoods`
- **Interactive Docs**: http://localhost:8000/docs

## 📝 Notes

- **Secrets**: Never commit secrets. `etl/config.yaml` is gitignored.
- **Database**: PostGIS extension required for geospatial operations
- **ETL**: Idempotent loads prevent duplicate data issues
- **Performance**: Optimized for sub-second API responses

## 🚀 Next Steps

- **Frontend Development**: React components for interactive mapping
- **Analytics**: Implement hotspot detection and trend analysis
- **Performance**: Add caching and database indexing
- **Security**: Implement rate limiting and authentication
- **Monitoring**: Add structured logging and metrics
