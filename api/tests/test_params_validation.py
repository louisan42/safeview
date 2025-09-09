from fastapi.testclient import TestClient

from api.main import app


class TestIncidentsEndpointBboxValidation:
    """Unit tests for incidents endpoint bbox parameter validation"""
    
    def test_incidents_endpoint_with_insufficient_bbox_coordinates(self):
        """Test incidents endpoint validation with insufficient bbox coordinates"""
        client = TestClient(app)
        response = client.get("/v1/incidents?bbox=1,2,3")
        assert response.status_code == 422
        assert "bbox" in response.json()["detail"].lower()
    
    def test_incidents_endpoint_with_non_numeric_bbox_coordinates(self):
        """Test incidents endpoint validation with non-numeric bbox coordinates"""
        client = TestClient(app)
        response = client.get("/v1/incidents?bbox=a,b,c,d")
        assert response.status_code == 422
        assert "numbers" in response.json()["detail"].lower()
    
    def test_incidents_endpoint_with_invalid_bbox_coordinate_order(self):
        """Test incidents endpoint validation with invalid bbox coordinate order"""
        client = TestClient(app)
        response = client.get("/v1/incidents?bbox=10,10,0,0")
        assert response.status_code == 422
        assert "min < max" in response.json()["detail"].lower()


class TestIncidentsEndpointDateValidation:
    """Unit tests for incidents endpoint date parameter validation"""
    
    def test_incidents_endpoint_with_invalid_date_range_order(self):
        """Test incidents endpoint validation with date_from after date_to"""
        client = TestClient(app)
        response = client.get("/v1/incidents?date_from=2025-01-02&date_to=2025-01-01")
        assert response.status_code == 422
        assert "date_from" in response.json()["detail"].lower()


class TestIncidentsEndpointLimitValidation:
    """Unit tests for incidents endpoint limit parameter validation"""
    
    def test_incidents_endpoint_with_limit_below_minimum(self):
        """Test incidents endpoint validation with limit parameter below minimum"""
        client = TestClient(app)
        response = client.get("/v1/incidents?limit=0")
        assert response.status_code == 422
    
    def test_incidents_endpoint_with_limit_above_maximum(self):
        """Test incidents endpoint validation with limit parameter above maximum"""
        client = TestClient(app)
        response = client.get("/v1/incidents?limit=999999")
        assert response.status_code == 422
