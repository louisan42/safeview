import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from api.main import app


class TestInMemoryIntegration:
    """Integration tests using mocked database responses"""
    
    @pytest.fixture
    def mock_incidents_data(self):
        """Sample incidents data for testing"""
        return [
            {
                "id": 1,
                "dataset": "robbery",
                "event_unique_id": "E001",
                "report_date": "2024-01-01T10:00:00Z",
                "occ_date": "2024-01-01T09:30:00Z",
                "offence": "Robbery",
                "mci_category": "Robbery",
                "hood_158": "001",
                "lon": -79.4,
                "lat": 43.7,
                "geometry": None
            },
            {
                "id": 2,
                "dataset": "theft_over",
                "event_unique_id": "E002",
                "report_date": "2024-01-02T14:00:00Z",
                "occ_date": "2024-01-02T13:45:00Z",
                "offence": "Theft Over",
                "mci_category": "Theft Over",
                "hood_158": "002",
                "lon": -79.3,
                "lat": 43.6,
                "geometry": None
            }
        ]
    
    @pytest.fixture
    def mock_neighbourhoods_data(self):
        """Sample neighbourhoods data for testing"""
        return [
            {
                "area_long_code": "001",
                "area_short_code": "1",
                "area_name": "Downtown",
                "geometry": None
            },
            {
                "area_long_code": "002",
                "area_short_code": "2", 
                "area_name": "Midtown",
                "geometry": None
            }
        ]
    
    def create_mock_cursor(self, data=None, count_result=None):
        """Create a mock cursor with specified data"""
        cursor_mock = AsyncMock()
        cursor_mock.fetchall.return_value = data or []
        cursor_mock.fetchone.return_value = count_result or {"count": len(data) if data else 0}
        cursor_mock.__aenter__ = AsyncMock(return_value=cursor_mock)
        cursor_mock.__aexit__ = AsyncMock(return_value=None)
        return cursor_mock
    
    def test_incidents_with_inmemory_db(self, mock_incidents_data):
        """Test incidents endpoint with mocked data"""
        client = TestClient(app)
        
        def mock_cursor():
            return self.create_mock_cursor(mock_incidents_data, {"count": 2})
        
        with patch('api.routers.incidents.cursor', mock_cursor):
            response = client.get("/v1/incidents?dataset=robbery")
            assert response.status_code == 200
            data = response.json()
            assert data["type"] == "FeatureCollection"
    
    def test_neighbourhoods_with_inmemory_db(self, mock_neighbourhoods_data):
        """Test neighbourhoods endpoint with mocked data"""
        client = TestClient(app)
        
        def mock_cursor():
            return self.create_mock_cursor(mock_neighbourhoods_data, {"count": 2})
        
        with patch('api.routers.neighbourhoods.cursor', mock_cursor):
            response = client.get("/v1/neighbourhoods")
            assert response.status_code == 200
            data = response.json()
            assert data["type"] == "FeatureCollection"
    
    def test_health_with_inmemory_db(self):
        """Test health endpoint with mocked database"""
        client = TestClient(app)
        
        async def mock_ping():
            return True
        
        with patch('api.routers.health.ping', mock_ping):
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["ok"] is True
    
    def test_analytics_with_inmemory_db(self):
        """Test analytics endpoint with mocked data"""
        client = TestClient(app)
        
        def mock_cursor():
            cursor_mock = AsyncMock()
            # Mock different queries that analytics endpoint makes
            def execute_handler(sql, params=None):
                if "COUNT(*) AS c" in sql and "GROUP BY" not in sql:
                    cursor_mock.fetchone.return_value = {"c": 10}
                elif "GROUP BY dataset" in sql:
                    cursor_mock.fetchall.return_value = [
                        {"dataset": "robbery", "c": 5},
                        {"dataset": "theft_over", "c": 3}
                    ]
                elif "GROUP BY mci_category" in sql:
                    cursor_mock.fetchall.return_value = [
                        {"mci_category": "Robbery", "c": 5},
                        {"mci_category": "Theft Over", "c": 3}
                    ]
                else:
                    cursor_mock.fetchall.return_value = []
                    cursor_mock.fetchone.return_value = {"c": 0}
            
            cursor_mock.execute.side_effect = execute_handler
            cursor_mock.__aenter__ = AsyncMock(return_value=cursor_mock)
            cursor_mock.__aexit__ = AsyncMock(return_value=None)
            return cursor_mock
        
        with patch('api.routers.analytics.cursor', mock_cursor):
            response = client.get("/v1/analytics?date_from=2024-01-01&date_to=2024-12-31")
            assert response.status_code == 200
            data = response.json()
            assert "totals" in data
            assert "by_dataset" in data["totals"]
            assert data["totals"]["total"] > 0  # Should have some incidents
