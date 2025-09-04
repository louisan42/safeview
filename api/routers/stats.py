from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..db import cursor

router = APIRouter(prefix="/stats", tags=["stats"])


class CountBy(BaseModel):
    key: Optional[str] = Field(None, description="Grouping key (e.g., dataset or mci_category)")
    count: int


class DailyCount(BaseModel):
    day: str
    count: int


class StatsResponse(BaseModel):
    total_incidents: int
    by_dataset: List[CountBy]
    by_mci_category: List[CountBy]
    last_30d: List[DailyCount]


@router.get(
    "",
    response_model=StatsResponse,
    summary="High-level incident statistics for dashboards",
    responses={
        200: {
            "description": "Totals and simple breakdowns for dashboard widgets",
            "content": {
                "application/json": {
                    "examples": {
                        "sample": {
                            "value": {
                                "total_incidents": 12345,
                                "by_dataset": [{"key": "robbery", "count": 234}],
                                "by_mci_category": [{"key": "Robbery", "count": 234}],
                                "last_30d": [{"day": "2025-08-05", "count": 12}],
                            }
                        }
                    }
                }
            },
        }
    },
)
async def get_stats() -> Dict[str, Any]:
    # total incidents
    async with cursor() as cur:
        await cur.execute("SELECT COUNT(*) AS total FROM tps_incidents")
        row = await cur.fetchone()
        total = int(row["total"]) if row and "total" in row else 0

    # by dataset
    async with cursor() as cur:
        await cur.execute(
            """
            SELECT dataset AS key, COUNT(*) AS count
            FROM tps_incidents
            GROUP BY dataset
            ORDER BY count DESC NULLS LAST
            """
        )
        by_dataset = await cur.fetchall()

    # by major crime category
    async with cursor() as cur:
        await cur.execute(
            """
            SELECT mci_category AS key, COUNT(*) AS count
            FROM tps_incidents
            GROUP BY mci_category
            ORDER BY count DESC NULLS LAST
            """
        )
        by_cat = await cur.fetchall()

    # last 30 days daily counts (based on report_date)
    async with cursor() as cur:
        await cur.execute(
            """
            SELECT to_char(date_trunc('day', report_date), 'YYYY-MM-DD') AS day,
                   COUNT(*) AS count
            FROM tps_incidents
            WHERE report_date >= NOW() - INTERVAL '30 days'
            GROUP BY 1
            ORDER BY 1
            """
        )
        last_30d = await cur.fetchall()

    def _normalize(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [dict(r) for r in rows] if rows else []

    return {
        "total_incidents": total,
        "by_dataset": _normalize(by_dataset),
        "by_mci_category": _normalize(by_cat),
        "last_30d": _normalize(last_30d),
    }
