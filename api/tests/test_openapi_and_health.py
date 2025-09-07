from fastapi.testclient import TestClient

from api.main import app


def test_openapi_schema_available():
    client = TestClient(app)
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert schema.get("openapi")
    assert schema.get("info", {}).get("title") == "SafetyView API"


def test_swagger_ui_available():
    client = TestClient(app)
    resp = client.get("/docs")
    assert resp.status_code == 200
    # Content contains swagger resources
    assert "swagger" in resp.text.lower()
