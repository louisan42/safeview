from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    # For Docker/production (running from /app directory)
    from routers.health import router as health_router
    from routers.incidents import router as incidents_router
    from routers.neighbourhoods import router as neighbourhoods_router
    from routers.stats import router as stats_router
    from routers.analytics import router as analytics_router
    from config import settings
except ImportError:
    # For tests/development (running from project root)
    from api.routers.health import router as health_router
    from api.routers.incidents import router as incidents_router
    from api.routers.neighbourhoods import router as neighbourhoods_router
    from api.routers.stats import router as stats_router
    from api.routers.analytics import router as analytics_router
    from api.config import settings

app = FastAPI(
    title="SafetyView API",
    version="0.1.0",
    description=(
        "Open, city-agnostic crime and safety analytics API. "
        "Provides incidents, regions, and analytics endpoints (per-capita, hotspots, anomalies, safety index)."
    ),
    contact={
        "name": "SafetyView",
        "url": "https://github.com/louisan42/safeview",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/license/mit",
    },
    terms_of_service="https://github.com/louisan42/safeview/blob/main/LICENSE",
)

# CORS: restricted to known origins for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(health_router)
app.include_router(incidents_router, prefix="/v1")
app.include_router(neighbourhoods_router, prefix="/v1")
app.include_router(stats_router, prefix="/v1")
app.include_router(analytics_router)


# For `python -m api.main`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8888, reload=True)
