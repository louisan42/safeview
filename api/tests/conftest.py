# Ensure the project root is on sys.path for `import api` during local pytest runs
import os
import sys
import pytest
from unittest.mock import AsyncMock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture
def mock_db_cursor():
    """Reusable mock database cursor for tests"""
    cursor = AsyncMock()
    cursor.fetchall = AsyncMock(return_value=[])
    cursor.fetchone = AsyncMock(return_value=None)
    cursor.execute = AsyncMock()
    cursor.__aenter__ = AsyncMock(return_value=cursor)
    cursor.__aexit__ = AsyncMock(return_value=None)
    return cursor


@pytest.fixture
def mock_cursor_factory():
    """Factory for creating mock cursors with specific return values"""
    def _factory(fetchall_return=None, fetchone_return=None):
        cursor = AsyncMock()
        cursor.fetchall = AsyncMock(return_value=fetchall_return or [])
        cursor.fetchone = AsyncMock(return_value=fetchone_return)
        cursor.execute = AsyncMock()
        cursor.__aenter__ = AsyncMock(return_value=cursor)
        cursor.__aexit__ = AsyncMock(return_value=None)
        return cursor
    return _factory
