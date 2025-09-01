from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from ..db import cursor

router = APIRouter(prefix="/neighbourhoods", tags=["neighbourhoods"])  # city-agnostic schema


class GeoJSONGeometry(BaseModel):
    type: str
    coordinates: Any


class Feature(BaseModel):
    type: str = Field(default="Feature")
    geometry: Optional[GeoJSONGeometry] | Dict[str, Any] | None
    properties: Dict[str, Any]


class FeatureCollection(BaseModel):
    type: str = Field(default="FeatureCollection")
    features: List[Feature]


def _fc(features: List[Dict[str, Any]]):
    return {"type": "FeatureCollection", "features": features}


class ErrorResponse(BaseModel):
    detail: str


@router.get(
    "",
    response_model=FeatureCollection,
    responses={422: {"model": ErrorResponse, "description": "Validation error"}},
)
async def list_neighbourhoods(
    code: Optional[str] = Query(None, description="Filter by area_long_code or area_short_code", examples={"sample": {"value": "001"}}),
    bbox: Optional[str] = Query(None, description="minLon,minLat,maxLon,maxLat", examples={"sample": {"value": "-79.6,43.6,-79.3,43.8"}}),
):
    where = ["1=1"]
    params: List[Any] = []

    if code:
        where.append("(area_long_code = %s OR area_short_code = %s)")
        params.extend([code, code])

    if bbox:
        parts = bbox.split(",")
        if len(parts) != 4:
            raise HTTPException(status_code=422, detail="bbox must be 'minLon,minLat,maxLon,maxLat'")
        try:
            minx, miny, maxx, maxy = [float(x) for x in parts]
        except ValueError:
            raise HTTPException(status_code=422, detail="bbox coordinates must be numbers")
        if minx >= maxx or miny >= maxy:
            raise HTTPException(status_code=422, detail="bbox must have min < max for both lon and lat")
        where.append("ST_Intersects(geom, ST_MakeEnvelope(%s,%s,%s,%s,4326))")
        params.extend([minx, miny, maxx, maxy])

    where_sql = " AND ".join(where)

    sql = f"""
        SELECT
          area_long_code, area_short_code, area_name,
          ST_AsGeoJSON(geom)::json AS geometry
        FROM cot_neighbourhoods_158
        WHERE {where_sql}
        ORDER BY area_long_code
    """

    async with cursor() as cur:
        await cur.execute(sql, params)
        rows = await cur.fetchall()

    features = [
        {
            "type": "Feature",
            "geometry": r.get("geometry"),
            "properties": {
                "area_long_code": r.get("area_long_code"),
                "area_short_code": r.get("area_short_code"),
                "area_name": r.get("area_name"),
            },
        }
        for r in rows
    ]
    return _fc(features)
