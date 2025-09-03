from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from ..db import cursor

router = APIRouter(prefix="/incidents", tags=["incidents"])


class GeoJSONGeometry(BaseModel):
    """GeoJSON geometry object (supports Point/Polygon/etc.)."""
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


class BBox(BaseModel):
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float


class ErrorResponse(BaseModel):
    detail: str


def _to_geojson(features: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": f.pop("geometry"),
                "properties": f,
            }
            for f in features
        ],
    }


@router.get(
    "",
    response_model=FeatureCollection,
    summary="List incidents with filters, sorting, pagination, and GeoJSON output",
    responses={
        200: {
            "description": "GeoJSON FeatureCollection of incidents",
            "content": {
                "application/json": {
                    "examples": {
                        "sample": {
                            "value": {
                                "type": "FeatureCollection",
                                "total": 123,
                                "features": [
                                    {
                                        "type": "Feature",
                                        "geometry": {"type": "Point", "coordinates": [-79.4, 43.7]},
                                        "properties": {
                                            "id": 123,
                                            "dataset": "robbery",
                                            "report_date": "2025-01-01T00:00:00Z",
                                            "hood_158": "001"
                                        },
                                    }
                                ],
                            }
                        }
                    }
                }
            },
        },
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def list_incidents(
    dataset: Optional[str] = Query(
        None,
        description="robbery|theft_over|break_and_enter or other dataset tags",
        examples={"sample": {"value": "robbery"}},
    ),
    date_from: Optional[datetime] = Query(None, examples={"sample": {"value": "2025-01-01"}}),
    date_to: Optional[datetime] = Query(None, examples={"sample": {"value": "2025-01-31"}}),
    hood: Optional[str] = Query(None, description="Neighbourhood code", examples={"sample": {"value": "001"}}),
    bbox: Optional[str] = Query(None, description="minLon,minLat,maxLon,maxLat", examples={"sample": {"value": "-79.6,43.6,-79.3,43.8"}}),
    mci_category: Optional[str] = Query(None, description="Major crime category", examples={"sample": {"value": "Robbery"}}),
    offence: Optional[str] = Query(None, description="Offence contains (case-insensitive)", examples={"sample": {"value": "robbery"}}),
    event_unique_id: Optional[str] = Query(None, description="Exact event unique id", examples={"sample": {"value": "E1"}}),
    limit: int = Query(500, ge=1, le=5000, examples={"sample": {"value": 100}}),
    offset: int = Query(0, ge=0, examples={"sample": {"value": 0}}),
    as_geojson: bool = Query(True),
    sort_by: Optional[str] = Query(
        "report_date",
        description="Field to sort by (allowed: report_date, occ_date, id)",
        examples={"sample": {"value": "report_date"}},
    ),
    sort_dir: Optional[str] = Query(
        "desc",
        description="Sort direction (asc|desc)",
        examples={"sample": {"value": "desc"}},
    ),
):
    where = ["1=1"]
    params: List[Any] = []

    if dataset:
        where.append("dataset = %s")
        params.append(dataset)
    if date_from:
        where.append("report_date >= %s")
        params.append(date_from)
    if date_to:
        where.append("report_date <= %s")
        params.append(date_to)
    # Validate date range
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from cannot be after date_to")
    if hood:
        where.append("hood_158 = %s")
        params.append(hood)
    if mci_category:
        where.append("mci_category = %s")
        params.append(mci_category)
    if offence:
        where.append("offence ILIKE %s")
        params.append(f"%{offence}%")
    if event_unique_id:
        where.append("event_unique_id = %s")
        params.append(event_unique_id)

    bbox_sql = None
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
        bbox_sql = "ST_Intersects(geom, ST_MakeEnvelope(%s,%s,%s,%s,4326))"
        params.extend([minx, miny, maxx, maxy])

    if bbox_sql:
        where.append(bbox_sql)

    where_sql = " AND ".join(where)

    # Whitelist ORDER BY
    order_field_map = {
        "report_date": "report_date",
        "occ_date": "occ_date",
        "id": "id",
    }
    order_field = order_field_map.get((sort_by or "report_date").lower(), "report_date")
    order_dir = "DESC" if (sort_dir or "desc").lower() == "desc" else "ASC"

    # Count total before pagination
    count_sql = f"SELECT COUNT(*) AS total FROM tps_incidents WHERE {where_sql}"
    async with cursor() as cur:
        await cur.execute(count_sql, params)
        # Some test cursors only implement fetchall(); support both.
        try:
            total_row = await cur.fetchone()
        except AttributeError:
            rows_total = await cur.fetchall()
            total_row = rows_total[0] if rows_total else {"total": 0}
        total = int(total_row["total"]) if total_row and "total" in total_row else 0

    # Geo fields are nullable; build geometry only when lon/lat present, and emit GeoJSON directly
    sql = f"""
        SELECT
          id,
          dataset,
          event_unique_id,
          report_date,
          occ_date,
          offence,
          mci_category,
          hood_158,
          lon, lat,
          ST_AsGeoJSON(
            CASE WHEN ST_IsEmpty(geom) OR geom IS NULL THEN
              CASE WHEN lon IS NOT NULL AND lat IS NOT NULL THEN ST_SetSRID(ST_MakePoint(lon,lat),4326) ELSE NULL END
            ELSE geom END
          )::json AS geometry
        FROM tps_incidents
        WHERE {where_sql}
        ORDER BY {order_field} {order_dir} NULLS LAST, id {order_dir}
        LIMIT %s OFFSET %s
    """

    params.extend([limit, offset])

    async with cursor() as cur:
        await cur.execute(sql, params)
        rows = await cur.fetchall()

    if as_geojson:
        # Geometry already in GeoJSON via main query
        if not rows:
            return {"type": "FeatureCollection", "features": [], "total": total}
        features = []
        for r in rows:
            props = dict(r)
            geom = props.pop("geometry", None)
            if geom is None:
                # Fallback for tests/mocks or missing geom: use lon/lat when available
                lon_v = props.get("lon")
                lat_v = props.get("lat")
                if lon_v is not None and lat_v is not None:
                    geom = {"type": "Point", "coordinates": [float(lon_v), float(lat_v)]}
            features.append({"type": "Feature", "geometry": geom, "properties": props})
        return {"type": "FeatureCollection", "features": features, "total": total}

    return {"rows": rows, "count": len(rows), "total": total}
