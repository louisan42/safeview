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
        mock_conn.closed = False
        
        with patch('psycopg.AsyncConnection.connect', return_value=mock_conn) as mock_connect:
            with patch('api.db.settings') as mock_settings:
                mock_settings.PG_DSN = 'postgresql://test:test@localhost/test'
                # Reset the global pool to ensure fresh connection
                import api.db
                api.db._pool = None
                
                conn = await get_conn()
                assert conn == mock_conn
                mock_connect.assert_called_once_with('postgresql://test:test@localhost/test')
    
    @pytest.mark.asyncio
    async def test_get_conn_no_dsn(self):
        """Test connection when no DSN is configured"""
        with patch('psycopg.AsyncConnection.connect') as mock_connect:
            mock_connect.side_effect = TypeError("connect() missing required argument")
            with patch('api.db.settings') as mock_settings:
                mock_settings.PG_DSN = None
                # Reset the global pool to ensure fresh connection
                import api.db
                api.db._pool = None
                
                # psycopg raises TypeError when DSN is None, not AttributeError
                with pytest.raises(TypeError):
                    await get_conn()
