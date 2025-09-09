from fastapi.testclient import TestClient

from api.main import app


class TestNeighbourhoodsEndpointBboxValidation:
    """Unit tests for neighbourhoods endpoint bbox parameter validation"""
    
    def test_neighbourhoods_endpoint_with_insufficient_bbox_coordinates(self):
        """Test neighbourhoods endpoint validation with insufficient bbox coordinates"""
        client = TestClient(app)
        response = client.get("/v1/neighbourhoods?bbox=1,2,3")
        assert response.status_code == 422
        assert "bbox" in response.json()["detail"].lower()
    
    def test_neighbourhoods_endpoint_with_non_numeric_bbox_coordinates(self):
        """Test neighbourhoods endpoint validation with non-numeric bbox coordinates"""
        client = TestClient(app)
        response = client.get("/v1/neighbourhoods?bbox=a,b,c,d")
        assert response.status_code == 422
        assert "numbers" in response.json()["detail"].lower()
    
    def test_neighbourhoods_endpoint_with_invalid_bbox_coordinate_order(self):
        """Test neighbourhoods endpoint validation with invalid bbox coordinate order"""
        client = TestClient(app)
        response = client.get("/v1/neighbourhoods?bbox=10,10,0,0")
        assert response.status_code == 422
        assert "min < max" in response.json()["detail"].lower()
