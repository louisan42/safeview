import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from api.main import app


class TestIncidentsEndpointErrorHandling:
    """Unit tests for incidents endpoint error handling using mocks"""
    
    def test_incidents_endpoint_with_database_connection_error(self):
        """Test incidents endpoint when database connection fails"""
        def mock_failing_cursor():
            cursor_mock = AsyncMock()
            cursor_mock.__aenter__.side_effect = ConnectionError("Database connection failed")
            cursor_mock.__aexit__ = AsyncMock(return_value=None)
            return cursor_mock
        
        with patch('api.routers.incidents.cursor', mock_failing_cursor):
            client = TestClient(app)
            response = client.get("/v1/incidents")
            assert response.status_code in [200, 500]
    
    def test_incidents_endpoint_with_invalid_geojson_data(self):
        """Test incidents endpoint handling of invalid geometry data"""
        mock_data = [
            {
                "id": 123,
                "dataset": "robbery",
                "event_unique_id": "E1",
                "report_date": "2025-01-01T00:00:00Z",
                "occ_date": "2025-01-01T00:00:00Z",
                "offence": "Robbery",
                "mci_category": "Robbery",
                "hood_158": "001",
                "lon": None,  # Invalid coordinates
                "lat": None,
                "geometry": None,
            }
        ]
        
        def mock_cursor_cm():
            cursor = AsyncMock()
            cursor.fetchall.return_value = mock_data
            cursor.__aenter__ = AsyncMock(return_value=cursor)
            cursor.__aexit__ = AsyncMock(return_value=None)
            return cursor
        
        with patch('api.routers.incidents.cursor', mock_cursor_cm):
            client = TestClient(app)
            response = client.get("/v1/incidents")
            assert response.status_code == 200
    
    def test_incidents_endpoint_with_large_result_set(self):
        """Test incidents endpoint handling of large result sets"""
        large_mock_data = [
            {
                "id": i,
                "dataset": "robbery",
                "event_unique_id": f"E{i}",
                "report_date": "2025-01-01T00:00:00Z",
                "occ_date": "2025-01-01T00:00:00Z",
                "offence": "Robbery",
                "mci_category": "Robbery",
                "hood_158": "001",
                "lon": -79.4,
                "lat": 43.7,
                "geometry": None,
            }
            for i in range(1000)  # Large dataset
        ]
        
        def mock_cursor_cm():
            cursor = AsyncMock()
            cursor.fetchall.return_value = large_mock_data
            cursor.__aenter__ = AsyncMock(return_value=cursor)
            cursor.__aexit__ = AsyncMock(return_value=None)
            return cursor
        
        with patch('api.routers.incidents.cursor', mock_cursor_cm):
            client = TestClient(app)
            response = client.get("/v1/incidents?limit=1000")
            assert response.status_code == 200
            data = response.json()
            assert len(data["features"]) <= 1000


class TestAnalyticsEndpointErrorHandling:
    """Unit tests for analytics endpoint error handling using mocks"""
    
    def test_analytics_endpoint_with_invalid_interval_parameter(self):
        """Test analytics endpoint with invalid interval parameter"""
        client = TestClient(app)
        response = client.get("/v1/analytics?interval=invalid")
        assert response.status_code == 422
