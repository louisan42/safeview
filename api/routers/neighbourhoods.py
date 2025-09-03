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
    total: Optional[int] = Field(default=None, description="Total rows matching filters (ignores limit/offset)")


def _fc(features: List[Dict[str, Any]]):
    return {"type": "FeatureCollection", "features": features}


class ErrorResponse(BaseModel):
    detail: str


@router.get(
    "",
    response_model=FeatureCollection,
    summary="List neighbourhoods with optional code/bbox filters, sorting and pagination",
    responses={
        200: {
            "description": "GeoJSON FeatureCollection of neighbourhoods",
            "content": {
                "application/json": {
                    "examples": {
                        "sample": {
                            "value": {
                                "type": "FeatureCollection",
                                "total": 1,
                                "features": [
                                    {
                                        "type": "Feature",
                                        "geometry": {"type": "Polygon", "coordinates": [[[0,0],[1,0],[1,1],[0,1],[0,0]]]},
                                        "properties": {
                                            "area_long_code": "001",
                                            "area_short_code": "1",
                                            "area_name": "Test Region"
                                        },
                                    }
                                ],
                            }
                        }
                    }
                }
            },
        },
        422: {"model": ErrorResponse, "description": "Validation error"}
    },
)
async def list_neighbourhoods(
    code: Optional[str] = Query(None, description="Filter by area_long_code or area_short_code", examples={"sample": {"value": "001"}}),
    bbox: Optional[str] = Query(None, description="minLon,minLat,maxLon,maxLat", examples={"sample": {"value": "-79.6,43.6,-79.3,43.8"}}),
    limit: int = Query(500, ge=1, le=5000, examples={"sample": {"value": 100}}),
    offset: int = Query(0, ge=0, examples={"sample": {"value": 0}}),
    sort_by: Optional[str] = Query(
        "area_long_code",
        description="Field to sort by (allowed: area_long_code, area_short_code, area_name)",
        examples={"sample": {"value": "area_long_code"}},
    ),
    sort_dir: Optional[str] = Query(
        "asc",
        description="Sort direction (asc|desc)",
        examples={"sample": {"value": "asc"}},
    ),
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

    # Whitelist ORDER BY
    order_field_map = {
        "area_long_code": "area_long_code",
        "area_short_code": "area_short_code",
        "area_name": "area_name",
    }
    order_field = order_field_map.get((sort_by or "area_long_code").lower(), "area_long_code")
    order_dir = "ASC" if (sort_dir or "asc").lower() == "asc" else "DESC"

    # Count total
    count_sql = f"SELECT COUNT(*) AS total FROM cot_neighbourhoods_158 WHERE {where_sql}"
    async with cursor() as cur:
        await cur.execute(count_sql, params)
        try:
            total_row = await cur.fetchone()
        except AttributeError:
            all_rows = await cur.fetchall()
            total_row = all_rows[0] if all_rows else {"total": 0}
        total = int(total_row["total"]) if total_row and "total" in total_row else 0

    sql = f"""
        SELECT
          area_long_code, area_short_code, area_name,
          ST_AsGeoJSON(geom)::json AS geometry
        FROM cot_neighbourhoods_158
        WHERE {where_sql}
        ORDER BY {order_field} {order_dir}
        LIMIT %s OFFSET %s
    """

    params_rows = [*params, limit, offset]
    async with cursor() as cur:
        await cur.execute(sql, params_rows)
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
    fc = _fc(features)
    fc["total"] = total
    return fc
