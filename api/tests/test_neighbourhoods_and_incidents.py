from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from api.main import app


class TestNeighbourhoodsEndpointGeojsonResponse:
    """Unit tests for neighbourhoods endpoint GeoJSON response using mocks"""
    
    def test_neighbourhoods_endpoint_returns_valid_geojson_structure(self, monkeypatch):
        """Test neighbourhoods endpoint returns valid GeoJSON structure"""
        def mock_cursor_cm():
            cursor = AsyncMock()
            cursor.fetchall.return_value = [
                {
                    "area_long_code": "001",
                    "area_short_code": "1",
                    "area_name": "Test Neighbourhood",
                    # Router expects 'geometry' field alias
                    "geometry": {"type": "Polygon", "coordinates": [[[0,0],[1,0],[1,1],[0,1],[0,0]]]},
                }
            ]
            cursor.__aenter__ = AsyncMock(return_value=cursor)
            cursor.__aexit__ = AsyncMock(return_value=None)
            return cursor
        
        import api.routers.neighbourhoods as neighbourhoods_module
        monkeypatch.setattr(neighbourhoods_module, 'cursor', mock_cursor_cm)
        
        client = TestClient(app)
        response = client.get("/v1/neighbourhoods")
        assert response.status_code == 200
        body = response.json()
        assert body["type"] == "FeatureCollection"
        assert "features" in body
        assert len(body["features"]) >= 1  # Accept any valid response with features
        feature = body["features"][0]
        assert feature["type"] == "Feature"
        assert feature["geometry"] is not None
        assert feature["geometry"]["type"] in ["Polygon", "Point"]
        assert "area_long_code" in feature["properties"]


class TestIncidentsEndpointGeojsonResponse:
    """Unit tests for incidents endpoint GeoJSON response using mocks"""
    
    def test_incidents_endpoint_returns_valid_geojson_structure(self):
        """Test incidents endpoint returns valid GeoJSON FeatureCollection structure"""
        mock_data = [
            {
                "id": 1,
                "dataset": "robbery",
                "event_unique_id": "E1",
                "report_date": "2024-01-01T00:00:00Z",
                "occ_date": "2024-01-01T00:00:00Z",
                "offence": "Robbery",
                "mci_category": "Robbery",
                "hood_158": "001",
                "lon": -79.4,
                "lat": 43.7,
                "geojson": {"type": "Point", "coordinates": [-79.4, 43.7]},
            }
        ]
        
        def mock_cursor_cm():
            cursor = AsyncMock()
            cursor.fetchall.return_value = mock_data
            cursor.fetchone.return_value = {"count": 1}
            cursor.__aenter__ = AsyncMock(return_value=cursor)
            cursor.__aexit__ = AsyncMock(return_value=None)
            return cursor
        
        with patch('api.routers.incidents.cursor', mock_cursor_cm):
            client = TestClient(app)
            response = client.get("/v1/incidents?limit=1")
            assert response.status_code == 200
            body = response.json()
            assert body["type"] == "FeatureCollection"
            assert len(body["features"]) == 1
            feature = body["features"][0]
            assert feature["geometry"]["type"] == "Point"
            assert "dataset" in feature["properties"]
            assert "id" in feature["properties"]
