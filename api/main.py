import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.routers.analytics import router as analytics_router
from api.routers.geocode import router as geocode_router
from api.routers.health import router as health_router
from api.routers.incidents import router as incidents_router
from api.routers.neighbourhoods import router as neighbourhoods_router
from api.routers.stats import router as stats_router
from api.sanitize import install_log_redaction

install_log_redaction()

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
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(health_router)
app.include_router(incidents_router, prefix="/v1")
app.include_router(neighbourhoods_router, prefix="/v1")
app.include_router(stats_router, prefix="/v1")
app.include_router(analytics_router)
app.include_router(geocode_router, prefix="/v1")


# For `python -m api.main` (loopback by default; Docker/Railway bind 0.0.0.0 via CMD)
if __name__ == "__main__":
    host = os.getenv("UVICORN_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8888"))
    uvicorn.run("api.main:app", host=host, port=port, reload=True)
