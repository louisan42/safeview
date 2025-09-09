import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime

from api.main import app


class TestStatsEndpointBasicResponse:
    """Unit tests for stats endpoint basic response using mocks"""
    
    def test_stats_endpoint_returns_correct_response_structure(self):
        """Test stats endpoint returns expected JSON response structure"""
        def mock_cursor_cm():
            cursor = AsyncMock()
            # Mock different queries that stats endpoint makes
            def execute_handler(sql, params=None):
                if "COUNT(*) AS total" in sql:
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
            client = TestClient(app)
            response = client.get("/v1/stats")
            assert response.status_code == 200
            data = response.json()
            assert "total_incidents" in data
            assert isinstance(data["total_incidents"], int)


class TestStatsEndpointWithDatasetFilter:
    """Unit tests for stats endpoint with dataset filtering using mocks"""
    
    def test_stats_endpoint_with_dataset_filter_parameter(self):
        """Test stats endpoint when filtering by specific dataset"""
        def mock_cursor_cm():
            cursor = AsyncMock()
            # Mock different queries that stats endpoint makes
            def execute_handler(sql, params=None):
                if "COUNT(*) AS total" in sql:
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
            client = TestClient(app)
            response = client.get("/v1/stats?dataset=robbery")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data["total_incidents"], int)
