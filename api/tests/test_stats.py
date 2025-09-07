import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime

from api.main import app


class TestStats:
    """Test suite for stats endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_stats_basic_response(self, client, monkeypatch):
        """Test basic stats endpoint response structure"""
        def mock_cursor_cm():
            cursor = AsyncMock()
            # Mock different queries that stats endpoint makes
            def execute_handler(sql, params=None):
                if "COUNT(*) AS total" in sql:
                    from datetime import datetime
                    cursor.fetchone.return_value = {
                        "total": 50000,
                        "min_dt": datetime.fromisoformat("2020-01-01T00:00:00"),
                        "max_dt": datetime.fromisoformat("2024-12-31T23:59:59")
                    }
                elif "etl_metadata" in sql:
                    cursor.fetchone.return_value = {"value": "2024-01-01T12:00:00Z"}
                else:
                    cursor.fetchall.return_value = []
                    cursor.fetchone.return_value = None
            
            cursor.execute.side_effect = execute_handler
            cursor.__aenter__ = AsyncMock(return_value=cursor)
            cursor.__aexit__ = AsyncMock(return_value=None)
            return cursor
        
        with patch('api.routers.stats.cursor', mock_cursor_cm):
            response = client.get("/v1/stats")
            assert response.status_code == 200
            data = response.json()
            assert "total_incidents" in data
            assert "by_dataset" in data
            assert "by_mci_category" in data
            assert data["total_incidents"] == 50000
    
    def test_stats_with_dataset_filter(self, client, monkeypatch):
        """Test stats with dataset filter"""
        def mock_cursor_cm():
            cursor = AsyncMock()
            # Mock different queries that stats endpoint makes
            def execute_handler(sql, params=None):
                if "COUNT(*) AS total" in sql:
                    from datetime import datetime
                    cursor.fetchone.return_value = {
                        "total": 10000,
                        "min_dt": datetime.fromisoformat("2020-01-01T00:00:00"),
                        "max_dt": datetime.fromisoformat("2024-12-31T23:59:59")
                    }
                elif "etl_metadata" in sql:
                    cursor.fetchone.return_value = {"value": "2024-01-01T12:00:00Z"}
                else:
                    cursor.fetchall.return_value = []
                    cursor.fetchone.return_value = None
            
            cursor.execute.side_effect = execute_handler
            cursor.__aenter__ = AsyncMock(return_value=cursor)
            cursor.__aexit__ = AsyncMock(return_value=None)
            return cursor
        
        with patch('api.routers.stats.cursor', mock_cursor_cm):
            response = client.get("/v1/stats?dataset=robbery")
            assert response.status_code == 200
            data = response.json()
            assert data["total_incidents"] == 10000
