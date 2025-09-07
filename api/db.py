from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

import psycopg
from psycopg.rows import dict_row

try:
    # For Docker/production (running from /app directory)
    from config import settings
except ImportError:
    # For tests/development (running from project root)
    from api.config import settings

# Simple async connection pool using psycopg "async" connection
# Note: psycopg (v3) supports async via psycopg.AsyncConnection

_pool: Optional[psycopg.AsyncConnection] = None


async def get_conn() -> psycopg.AsyncConnection:
    global _pool
    if _pool is None or _pool.closed:
        _pool = await psycopg.AsyncConnection.connect(settings.PG_DSN)
        try:
            _pool.autocommit = True  # avoid aborted transaction state across requests
        except Exception:
            pass
    return _pool


@asynccontextmanager
async def cursor(dict_rows: bool = True) -> AsyncIterator[psycopg.AsyncCursor]:
    conn = await get_conn()
    try:
        async with conn.cursor(row_factory=dict_row if dict_rows else None) as cur:
            yield cur
    except Exception:
        # Ensure we clear any failed transaction state so subsequent requests don't see
        # "current transaction is aborted" on this shared connection.
        try:
            await conn.rollback()
        except Exception:
            pass
        raise


async def ping() -> bool:
    try:
        async with cursor() as cur:
            await cur.execute("SELECT 1 AS ok")
            _ = await cur.fetchone()
        return True
    except Exception:
        return False
