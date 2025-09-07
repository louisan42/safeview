from fastapi.testclient import TestClient
from unittest.mock import patch

from api.main import app
import api.routers.health as health_router


async def _fake_ping() -> bool:
    return True


def test_health_ok():
    with patch('api.db.ping', return_value=True):
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("ok") is True
        assert body.get("service") == "api"


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
