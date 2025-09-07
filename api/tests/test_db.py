import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.db import get_conn, cursor
from api.config import Settings


class TestDatabase:
    """Test database connection and cursor management"""
    
    @pytest.mark.asyncio
    async def test_get_conn_success(self):
        """Test successful database connection"""
        mock_conn = AsyncMock()
        
        with patch('api.db.psycopg.AsyncConnection.connect', return_value=mock_conn):
            with patch('api.db.settings') as mock_settings:
                mock_settings.PG_DSN = 'postgresql://test:test@localhost/test'
                conn = await get_conn()
                assert conn == mock_conn
    
    @pytest.mark.asyncio
    async def test_get_conn_no_dsn(self):
        """Test connection when no DSN is configured"""
        with patch('api.db.settings') as mock_settings:
            mock_settings.PG_DSN = None
            # Current behavior - psycopg gets None and fails with AttributeError
            with pytest.raises(AttributeError):
                await get_conn()
