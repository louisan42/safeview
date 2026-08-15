import asyncio
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/geocode", tags=["geocode"])

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "SafetyView/0.1 (https://github.com/louisan42/safeview; Toronto civic safety map)"
# west, north, east, south — Toronto bounding box
TORONTO_VIEWBOX = "-79.639,43.855,-79.115,43.581"


class GeocodeHit(BaseModel):
    label: str
    lat: float
    lng: float


class GeocodeResponse(BaseModel):
    results: List[GeocodeHit] = Field(default_factory=list)


def _nominatim_search(q: str) -> List[Dict[str, Any]]:
    params = {
        "q": q,
        "format": "jsonv2",
        "limit": "5",
        "countrycodes": "ca",
        "viewbox": TORONTO_VIEWBOX,
        "bounded": "1",
        "addressdetails": "0",
    }
    url = NOMINATIM_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=8) as resp:
        return json.loads(resp.read().decode("utf-8"))


@router.get("", response_model=GeocodeResponse, summary="Forward-geocode an address in Toronto")
async def geocode(q: str = Query(..., min_length=2, max_length=200)):
    try:
        raw = await asyncio.to_thread(_nominatim_search, q)
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=502, detail="Geocoder unavailable") from e
    except Exception as e:
        raise HTTPException(status_code=502, detail="Geocoder unavailable") from e

    results: List[GeocodeHit] = []
    for item in raw or []:
        try:
            results.append(
                GeocodeHit(
                    label=str(item.get("display_name") or q),
                    lat=float(item["lat"]),
                    lng=float(item["lon"]),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return GeocodeResponse(results=results)
