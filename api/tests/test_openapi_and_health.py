from fastapi.testclient import TestClient

from api.main import app


class TestOpenApiDocumentation:
    """Unit tests for OpenAPI documentation endpoints"""
    
    def test_openapi_schema_endpoint_returns_valid_schema(self):
        """Test OpenAPI schema endpoint returns valid schema with correct title"""
        client = TestClient(app)
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema.get("openapi")
        assert schema.get("info", {}).get("title") == "SafetyView API"
    
    def test_swagger_ui_documentation_endpoint_accessible(self):
        """Test Swagger UI documentation endpoint is accessible"""
        client = TestClient(app)
        response = client.get("/docs")
        assert response.status_code == 200
        # Content contains swagger resources
        assert "swagger" in response.text.lower()
