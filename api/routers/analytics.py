from datetime import datetime
from typing import List, Optional, Literal, Dict, Any

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

try:
    # For Docker/production (running from /app directory)
    from db import cursor
except ImportError:
    # For tests/development (running from project root)
    from api.db import cursor

router = APIRouter(prefix="/v1", tags=["analytics"])


# ---- Models ----
class SeriesPoint(BaseModel):
    date: datetime
    count: int


class Totals(BaseModel):
    total: int
    by_dataset: Dict[str, int]
    by_category: Dict[str, int]


class AnalyticsResponse(BaseModel):
    totals: Totals
    timeline: List[SeriesPoint]


class CompareWindow(BaseModel):
    date_from: datetime
    date_to: datetime


class CompareResponse(BaseModel):
    window_a: AnalyticsResponse
    window_b: AnalyticsResponse
    delta_total: int
    delta_total_pct: Optional[float]


# ---- Helpers ----
VALID_INTERVALS = {"day": "day", "week": "week", "month": "month"}


def _build_filters(dataset: Optional[str], mci_category: Optional[str], offence: Optional[str], bbox: Optional[str]):
    clauses: List[str] = []
    params: List[Any] = []

    if dataset:
        params.append(dataset)
        clauses.append(f"dataset = %s")
    if mci_category:
        params.append(mci_category)
        clauses.append(f"mci_category = %s")
    if offence:
        params.append(f"%{offence}%")
        clauses.append(f"offence ILIKE %s")
    if bbox:
        try:
            west, south, east, north = [float(x) for x in bbox.split(",")]
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid bbox format; expected 'west,south,east,north'")
        # ST_MakeEnvelope(lon_min, lat_min, lon_max, lat_max, 4326)
        clauses.append("geom && ST_MakeEnvelope(%s,%s,%s,%s,4326)")
        params.extend([west, south, east, north])

    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params


async def _run_analytics(date_from: datetime, date_to: datetime, interval: str,
                         dataset: Optional[str], mci_category: Optional[str], offence: Optional[str], bbox: Optional[str]) -> AnalyticsResponse:
    if interval not in VALID_INTERVALS:
        raise HTTPException(status_code=400, detail="interval must be one of day|week|month")

    where_common, params = _build_filters(dataset, mci_category, offence, bbox)

    # Ensure date bounds
    params_total = params + [date_from, date_to]
    where_total = where_common + (" AND " if where_common else " WHERE ") + "report_date >= %s AND report_date < %s"

    async with cursor() as cur:
        # Totals
        await cur.execute(f"SELECT COUNT(*) AS c FROM tps_incidents {where_total}", params_total)
        row = await cur.fetchone()
        total = int(row["c"]) if row else 0

        await cur.execute(f"SELECT dataset, COUNT(*) AS c FROM tps_incidents {where_total} GROUP BY dataset ORDER BY c DESC", params_total)
        by_dataset_rows = await cur.fetchall()
        by_dataset = {r["dataset"]: int(r["c"]) for r in by_dataset_rows if r["dataset"] is not None}

        await cur.execute(f"SELECT COALESCE(mci_category,'other') AS cat, COUNT(*) AS c FROM tps_incidents {where_total} GROUP BY cat ORDER BY c DESC", params_total)
        by_cat_rows = await cur.fetchall()
        by_category = {r["cat"]: int(r["c"]) for r in by_cat_rows}

        # Time series
        await cur.execute(
            f"""
            SELECT date_trunc(%s, report_date) AS bucket, COUNT(*) AS c
            FROM tps_incidents
            {where_total}
            GROUP BY bucket
            ORDER BY bucket
            """,
            [interval] + params_total,
        )
        ts_rows = await cur.fetchall()
        timeline = [SeriesPoint(date=r["bucket"], count=int(r["c"])) for r in ts_rows]

    return AnalyticsResponse(totals=Totals(total=total, by_dataset=by_dataset, by_category=by_category), timeline=timeline)


# ---- Routes ----
@router.get("/analytics", response_model=AnalyticsResponse, summary="Analytics for incidents over a time range")
async def analytics(
    date_from: datetime = Query(..., description="Start of window (inclusive)"),
    date_to: datetime = Query(..., description="End of window (exclusive)"),
    interval: Literal["day", "week", "month"] = Query("day"),
    dataset: Optional[str] = Query(None),
    mci_category: Optional[str] = Query(None),
    offence: Optional[str] = Query(None, description="ILIKE contains"),
    bbox: Optional[str] = Query(None, description="west,south,east,north"),
):
    return await _run_analytics(date_from, date_to, interval, dataset, mci_category, offence, bbox)


@router.get("/compare", response_model=CompareResponse, summary="Compare two incident time windows")
async def compare(
    a_date_from: datetime = Query(...),
    a_date_to: datetime = Query(...),
    b_date_from: datetime = Query(...),
    b_date_to: datetime = Query(...),
    interval: Literal["day", "week", "month"] = Query("day"),
    dataset: Optional[str] = Query(None),
    mci_category: Optional[str] = Query(None),
    offence: Optional[str] = Query(None),
    bbox: Optional[str] = Query(None),
):
    a = await _run_analytics(a_date_from, a_date_to, interval, dataset, mci_category, offence, bbox)
    b = await _run_analytics(b_date_from, b_date_to, interval, dataset, mci_category, offence, bbox)
    delta = a.totals.total - b.totals.total
    pct = None
    if b.totals.total:
        pct = (delta / b.totals.total) * 100.0
    return CompareResponse(window_a=a, window_b=b, delta_total=delta, delta_total_pct=pct)
