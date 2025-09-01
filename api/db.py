from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

import psycopg
from psycopg.rows import dict_row

from .config import settings

# Simple async connection pool using psycopg "async" connection
# Note: psycopg (v3) supports async via psycopg.AsyncConnection

_pool: Optional[psycopg.AsyncConnection] = None


async def get_conn() -> psycopg.AsyncConnection:
    global _pool
    if _pool is None or _pool.closed:
        _pool = await psycopg.AsyncConnection.connect(settings.PG_DSN)
    return _pool


@asynccontextmanager
async def cursor(dict_rows: bool = True) -> AsyncIterator[psycopg.AsyncCursor]:
    conn = await get_conn()
    async with conn.cursor(row_factory=dict_row if dict_rows else None) as cur:
        yield cur


async def ping() -> bool:
    try:
        async with cursor() as cur:
            await cur.execute("SELECT 1 AS ok")
            _ = await cur.fetchone()
        return True
    except Exception:
        return False
