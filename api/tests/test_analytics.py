import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from api.main import app


class TestAnalytics:
    """Test suite for analytics endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_cursor(self):
        """Mock database cursor for analytics queries"""
        cursor = AsyncMock()
        cursor.fetchall = AsyncMock()
        cursor.fetchone = AsyncMock()
        return cursor
    
    def test_analytics_basic_response(self, client, monkeypatch):
        """Test basic analytics endpoint response structure"""
        def mock_cursor_cm():
            cursor = AsyncMock()
            # Mock different queries that analytics endpoint makes
            def execute_handler(sql, params=None):
                if "COUNT(*) AS c" in sql and "GROUP BY" not in sql:
                    cursor.fetchone.return_value = {"c": 100}
                elif "GROUP BY dataset" in sql:
                    cursor.fetchall.return_value = [
                        {"dataset": "robbery", "c": 50},
                        {"dataset": "theft_over", "c": 30}
                    ]
                elif "GROUP BY mci_category" in sql:
                    cursor.fetchall.return_value = [
                        {"mci_category": "Robbery", "c": 50},
                        {"mci_category": "Theft Over", "c": 30}
                    ]
                else:
                    cursor.fetchall.return_value = []
                    cursor.fetchone.return_value = {"c": 0}
            
            cursor.execute.side_effect = execute_handler
            cursor.__aenter__ = AsyncMock(return_value=cursor)
            cursor.__aexit__ = AsyncMock(return_value=None)
            return cursor
        
        with patch('api.routers.analytics.cursor', mock_cursor_cm):
            response = client.get("/v1/analytics?date_from=2024-01-01&date_to=2024-12-31")
            assert response.status_code == 200
            data = response.json()
            assert "totals" in data
            assert "timeline" in data
    
    def test_analytics_with_filters(self, client, monkeypatch):
        """Test analytics with date and bbox filters"""
        def mock_cursor_cm():
            cursor = AsyncMock()
            # Mock different queries that analytics endpoint makes
            def execute_handler(sql, params=None):
                if "COUNT(*) AS c" in sql and "GROUP BY" not in sql:
                    cursor.fetchone.return_value = {"c": 50}
                elif "GROUP BY dataset" in sql:
                    cursor.fetchall.return_value = [{"dataset": "robbery", "c": 50}]
                elif "GROUP BY mci_category" in sql:
                    cursor.fetchall.return_value = [{"mci_category": "Robbery", "c": 50}]
                else:
                    cursor.fetchall.return_value = []
                    cursor.fetchone.return_value = {"c": 0}
            
            cursor.execute.side_effect = execute_handler
            cursor.__aenter__ = AsyncMock(return_value=cursor)
            cursor.__aexit__ = AsyncMock(return_value=None)
            return cursor
        
        with patch('api.routers.analytics.cursor', mock_cursor_cm):
            response = client.get("/v1/analytics?date_from=2024-01-01&date_to=2024-12-31&bbox=-79.5,43.6,-79.3,43.8")
            assert response.status_code == 200
    
    def test_analytics_invalid_interval(self, client):
        """Test analytics with invalid interval parameter"""
        response = client.get("/v1/analytics?interval=invalid")
        assert response.status_code == 422
    
    def test_analytics_timeline_intervals(self, client, monkeypatch):
        """Test different timeline intervals (day, week, month)"""
        def mock_cursor_cm():
            cursor = AsyncMock()
            # Mock different queries that analytics endpoint makes
            def execute_handler(sql, params=None):
                if "COUNT(*) AS c" in sql and "GROUP BY" not in sql:
                    cursor.fetchone.return_value = {"c": 25}
                elif "GROUP BY dataset" in sql:
                    cursor.fetchall.return_value = [{"dataset": "robbery", "c": 15}]
                elif "GROUP BY cat" in sql or "AS cat" in sql:
                    cursor.fetchall.return_value = [{"cat": "Robbery", "c": 15}]
                else:
                    cursor.fetchall.return_value = [
                        {"bucket": "2024-01-01", "c": 10},
                        {"bucket": "2024-01-02", "c": 15}
                    ]
                    cursor.fetchone.return_value = {"c": 0}
            
            cursor.execute.side_effect = execute_handler
            cursor.__aenter__ = AsyncMock(return_value=cursor)
            cursor.__aexit__ = AsyncMock(return_value=None)
            return cursor
        
        with patch('api.routers.analytics.cursor', mock_cursor_cm):
            for interval in ['day', 'week', 'month']:
                response = client.get(f"/v1/analytics?interval={interval}&date_from=2024-01-01&date_to=2024-12-31")
                assert response.status_code == 200
                data = response.json()
                assert "timeline" in data
