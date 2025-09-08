import pytest
from fastapi.testclient import TestClient


class TestIncidentsEdgeCases:
    """Test edge cases and error paths in incidents router"""
    
    @pytest.fixture
    def client(self):
        from api.main import app
        return TestClient(app)
    
    def test_incidents_with_invalid_dataset_filter(self, client):
        """Test incidents endpoint with invalid dataset filtering"""
        response = client.get("/v1/incidents?dataset=nonexistent_dataset&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        # Should return empty features for non-existent dataset
        assert len(data["features"]) == 0
    
    def test_incidents_with_bbox_filter(self, client):
        """Test incidents endpoint with bounding box filtering"""
        # Use a bbox that should contain some incidents in Toronto
        response = client.get("/v1/incidents?bbox=-79.6,43.5,-79.4,43.7&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        # Should return some incidents within the bbox
        assert len(data["features"]) > 0  # Should have incidents in this Toronto bbox
        
        # Test that all returned features have geometry within the bbox
        for feature in data["features"]:
            if feature["geometry"] is not None:
                coords = feature["geometry"]["coordinates"]
                # Check longitude is within bbox
                assert -79.6 <= coords[0] <= -79.4
                # Check latitude is within bbox  
                assert 43.5 <= coords[1] <= 43.7
    
    def test_incidents_with_invalid_bbox(self, client):
        """Test incidents endpoint with invalid bounding box"""
        # Test with invalid bbox format
        response = client.get("/v1/incidents?bbox=invalid&limit=5")
        assert response.status_code == 422  # FastAPI returns 422 for validation errors
    
    def test_incidents_with_date_range_filter(self, client):
        """Test incidents endpoint with date range filtering"""
        # Use a date range that should have some incidents - use 2025 since that's what the data contains
        response = client.get("/v1/incidents?start_date=2025-01-01&end_date=2025-12-31&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        # Should return some incidents in 2025
        assert len(data["features"]) > 0
        
        # Test that all returned features have dates within the range
        for feature in data["features"]:
            report_date = feature["properties"]["report_date"]
            # Basic check that date is in 2025
            assert "2025" in report_date
    
    def test_incidents_with_invalid_date_format(self, client):
        """Test incidents endpoint with invalid date format"""
        response = client.get("/v1/incidents?start_date=invalid-date&limit=5")
        # API handles invalid dates gracefully, returns 200 with empty results
        assert response.status_code == 200
    
    def test_incidents_with_large_limit(self, client):
        """Test incidents endpoint with very large limit"""
        response = client.get("/v1/incidents?limit=1000")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        # Should be capped at reasonable limit (1000 based on router code)
        assert len(data["features"]) <= 1000
