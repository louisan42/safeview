from fastapi import APIRouter

from api.db import ping
from api.version import public_build

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    ok = await ping()
    return {
        "ok": ok,
        "service": "api",
        **public_build(),
        "db": "up" if ok else "down",
    }


@router.get("/meta")
async def meta():
    return {
        "name": "SafetyView API",
        **public_build(),
        "city_agnostic": True,
        "endpoints": [
            "/v1/health",
            "/v1/meta",
            "/v1/incidents",
            "/v1/neighbourhoods",
        ],
    }
