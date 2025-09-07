import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from api.main import app


class TestIncidentsEdgeCases:
    """Test edge cases and error paths in incidents router"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_incidents_with_invalid_geojson_handling(self, client, monkeypatch):
        """Test handling of invalid geometry data from database"""
        def mock_cursor_cm():
            cursor = AsyncMock()
            # Mock data with invalid geometry that would cause ST_AsGeoJSON to fail
            cursor.fetchall.return_value = [
                {
                    "id": 123,
                    "dataset": "robbery", 
                    "event_unique_id": "E1",
                    "report_date": "2025-01-01T00:00:00Z",
                    "occ_date": "2025-01-01T00:00:00Z",
                    "geojson": None,  # Invalid geometry
                    "mci_category": "Robbery"
                }
            ]
            cursor.__aenter__ = AsyncMock(return_value=cursor)
            cursor.__aexit__ = AsyncMock(return_value=None)
            return cursor
        
        monkeypatch.setattr('api.routers.incidents.cursor', mock_cursor_cm)
        
        response = client.get("/v1/incidents?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        # Should handle invalid geometry gracefully (None geometry becomes null in JSON)
        assert len(data["features"]) == 1  # Feature is included but with null geometry
        assert data["features"][0]["geometry"] is None
    
    def test_incidents_with_dataset_filter(self, client, monkeypatch):
        """Test incidents endpoint with dataset filtering"""
        def mock_cursor_cm():
            cursor = AsyncMock()
            cursor.fetchall.return_value = [
                {
                    "id": 456,
                    "dataset": "assault",
                    "event_unique_id": "E2", 
                    "report_date": "2025-01-02T00:00:00Z",
                    "occ_date": "2025-01-02T00:00:00Z",
                    "geojson": '{"type":"Point","coordinates":[-79.4,43.7]}',
                    "mci_category": "Assault"
                }
            ]
            cursor.__aenter__ = AsyncMock(return_value=cursor)
            cursor.__aexit__ = AsyncMock(return_value=None)
            return cursor
        
        monkeypatch.setattr('api.routers.incidents.cursor', mock_cursor_cm)
        
        response = client.get("/v1/incidents?dataset=assault&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) == 1
        assert data["features"][0]["properties"]["dataset"] == "assault"
    
    def test_incidents_with_bbox_filter(self, client, monkeypatch):
        """Test incidents endpoint with bounding box filtering"""
        def mock_cursor_cm():
            cursor = AsyncMock()
            cursor.fetchall.return_value = [
                {
                    "id": 789,
                    "dataset": "theft",
                    "event_unique_id": "E3",
                    "report_date": "2025-01-03T00:00:00Z", 
                    "occ_date": "2025-01-03T00:00:00Z",
                    "geojson": '{"type":"Point","coordinates":[-79.5,43.6]}',
                    "mci_category": "Theft"
                }
            ]
            cursor.__aenter__ = AsyncMock(return_value=cursor)
            cursor.__aexit__ = AsyncMock(return_value=None)
            return cursor
        
        monkeypatch.setattr('api.routers.incidents.cursor', mock_cursor_cm)
        
        response = client.get("/v1/incidents?bbox=-79.6,43.5,-79.4,43.7&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) == 1
    
    def test_incidents_with_date_range_filter(self, client, monkeypatch):
        """Test incidents endpoint with date range filtering"""
        def mock_cursor_cm():
            cursor = AsyncMock()
            cursor.fetchall.return_value = [
                {
                    "id": 101,
                    "dataset": "burglary",
                    "event_unique_id": "E4",
                    "report_date": "2024-06-15T00:00:00Z",
                    "occ_date": "2024-06-15T00:00:00Z", 
                    "geojson": '{"type":"Point","coordinates":[-79.3,43.8]}',
                    "mci_category": "Break and Enter"
                }
            ]
            cursor.__aenter__ = AsyncMock(return_value=cursor)
            cursor.__aexit__ = AsyncMock(return_value=None)
            return cursor
        
        monkeypatch.setattr('api.routers.incidents.cursor', mock_cursor_cm)
        
        response = client.get("/v1/incidents?start_date=2024-01-01&end_date=2024-12-31&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) == 1
