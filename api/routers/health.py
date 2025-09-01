from fastapi import APIRouter
from ..db import ping
from ..config import settings

router = APIRouter(tags=["health"])

@router.get("/health")
async def health():
    ok = await ping()
    return {
        "ok": ok,
        "service": "api",
        "version": "0.1.0",
        "db": "up" if ok else "down",
    }

@router.get("/meta")
async def meta():
    return {
        "name": "SafetyView API",
        "version": "0.1.0",
        "city_agnostic": True,
        "endpoints": [
            "/v1/health",
            "/v1/meta",
            "/v1/incidents",
            "/v1/neighbourhoods",
        ],
    }
