from datetime import datetime
import os
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from ..db import cursor

# Helper functions to reduce cognitive complexity
def _parse_dt(val: str | None) -> datetime | None:
    """Parse ISO datetime or date string; treat empty/None as None. Supports 'Z'."""
    if not val:
        return None
    s = val.strip()
    if not s:
        return None
    # Support both 'Z' and '+00:00' timezone formats
    if s.endswith('Z'):
        s = s[:-1] + '+00:00'
    # Try parsing as datetime first, then as date
    for fmt in ["%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"]:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: {val}")


def _build_where_clause_and_params(
    dataset: Optional[str],
    date_from: Optional[str], 
    date_to: Optional[str],
    hood: Optional[str],
    mci_category: Optional[str],
    offence: Optional[str],
    event_unique_id: Optional[str],
    bbox: Optional[str]
) -> tuple[str, list]:
    """Build WHERE clause and parameters for incidents query."""
    where = ["1=1"]
    params = []

    if dataset:
        where.append("dataset = %s")
        params.append(dataset)
        
    # Handle date filters
    dt_from = _parse_dt(date_from)
    dt_to = _parse_dt(date_to)
    if dt_from:
        where.append("report_date >= %s")
        params.append(dt_from)
    if dt_to:
        where.append("report_date <= %s")
        params.append(dt_to)
    # Validate date range
    if dt_from and dt_to and dt_from > dt_to:
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

    # Handle bbox filter
    if bbox:
        bbox_sql, bbox_params = _parse_bbox(bbox)
        where.append(bbox_sql)
        params.extend(bbox_params)

    return " AND ".join(where), params


def _parse_bbox(bbox: str) -> tuple[str, list]:
    """Parse and validate bbox parameter, return SQL and params."""
    parts = bbox.split(",")
    if len(parts) != 4:
        raise HTTPException(status_code=422, detail="bbox must be 'minLon,minLat,maxLon,maxLat'")
    try:
        minx, miny, maxx, maxy = [float(x) for x in parts]
    except ValueError:
        raise HTTPException(status_code=422, detail="bbox coordinates must be numbers")
    if minx >= maxx or miny >= maxy:
        raise HTTPException(status_code=422, detail="bbox must have min < max for both lon and lat")
    
    bbox_sql = "ST_Intersects(COALESCE(geom, ST_SetSRID(ST_MakePoint(lon,lat),4326)), ST_MakeEnvelope(%s,%s,%s,%s,4326))"
    return bbox_sql, [minx, miny, maxx, maxy]


def _get_order_clause(sort_by: Optional[str], sort_dir: Optional[str]) -> str:
    """Get ORDER BY clause with whitelisted fields."""
    order_field_map = {
        "report_date": "report_date",
        "occ_date": "occ_date",
        "id": "id",
    }
    order_field = order_field_map.get((sort_by or "report_date").lower(), "report_date")
    order_dir = "DESC" if (sort_dir or "desc").lower() == "desc" else "ASC"
    return f"{order_field} {order_dir} NULLS LAST, id {order_dir}"


async def _get_total_count(where_sql: str, params: list) -> int:
    """Get total count of incidents matching filters."""
    count_sql = f"SELECT COUNT(*) AS total FROM tps_incidents WHERE {where_sql}"
    async with cursor() as cur:
        await cur.execute(count_sql, params)
        try:
            total_row = await cur.fetchone()
        except AttributeError:
            rows_total = await cur.fetchall()
            total_row = rows_total[0] if rows_total else {"total": 0}
        return int(total_row["total"]) if total_row and "total" in total_row else 0


async def _debug_log_counts(debug: bool, where_sql: str, params: list, bbox: Optional[str], total: int):
    """Log debug information about query counts."""
    if not debug or os.getenv("ENVIRONMENT") != "development":
        return
        
    try:
        print(f"[INCIDENTS][debug] where={where_sql} params={params}")
        
        async with cursor() as cur:
            # Global count (no filters)
            await cur.execute("SELECT COUNT(*) AS c, MIN(report_date) AS min_dt, MAX(report_date) AS max_dt FROM tps_incidents")
            g = await cur.fetchone()
            
            # Bbox-only count (if bbox present)
            bbox_only = None
            if bbox:
                bbox_sql, bbox_params = _parse_bbox(bbox)
                await cur.execute(f"SELECT COUNT(*) AS c FROM tps_incidents WHERE {bbox_sql}", bbox_params)
                bbox_row = await cur.fetchone()
                bbox_only = int(bbox_row['c']) if bbox_row else None
                
            print(
                f"[INCIDENTS][debug] total_filtered={total} total_global={int(g['c']) if g else 'n/a'} "
                f"min_dt={g['min_dt'] if g else 'n/a'} max_dt={g['max_dt'] if g else 'n/a'} bbox_only={bbox_only}"
            )
    except Exception:
        pass


def _format_geojson_response(rows: list, total: int) -> dict:
    """Format rows as GeoJSON FeatureCollection."""
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
    date_from: Optional[str] = Query(None, examples={"sample": {"value": "2025-01-01"}}),
    date_to: Optional[str] = Query(None, examples={"sample": {"value": "2025-01-31"}}),
    hood: Optional[str] = Query(None, description="Neighbourhood code", examples={"sample": {"value": "001"}}),
    bbox: Optional[str] = Query(None, description="minLon,minLat,maxLon,maxLat", examples={"sample": {"value": "-79.6,43.6,-79.3,43.8"}}),
    mci_category: Optional[str] = Query(None, description="Major crime category", examples={"sample": {"value": "Robbery"}}),
    offence: Optional[str] = Query(None, description="Offence contains (case-insensitive)", examples={"sample": {"value": "robbery"}}),
    event_unique_id: Optional[str] = Query(None, description="Exact event unique id", examples={"sample": {"value": "E1"}}),
    limit: int = Query(500, ge=1, le=5000, examples={"sample": {"value": 100}}),
    offset: int = Query(0, ge=0, examples={"sample": {"value": 0}}),
    as_geojson: bool = Query(True),
    debug: Optional[bool] = Query(False, description="When true, logs where/params and counts for diagnosis"),
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
    # Build WHERE clause and parameters using helper function
    where_sql, params = _build_where_clause_and_params(
        dataset, date_from, date_to, hood, mci_category, offence, event_unique_id, bbox
    )
    
    # Get ORDER BY clause using helper function
    order_clause = _get_order_clause(sort_by, sort_dir)
    
    # Get total count
    total = await _get_total_count(where_sql, params)
    
    # Debug logging
    await _debug_log_counts(debug, where_sql, params, bbox, total)

    # Build and execute main query
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
        ORDER BY {order_clause}
        LIMIT %s OFFSET %s
    """

    query_params = params + [limit, offset]
    async with cursor() as cur:
        await cur.execute(sql, query_params)
        rows = await cur.fetchall()

    # Format response
    if as_geojson:
        return _format_geojson_response(rows, total)
    
    return {"rows": rows, "count": len(rows), "total": total}
