from fastapi.testclient import TestClient

from api.main import app


def _client():
    return TestClient(app)


def test_invalid_bbox_format():
    r = _client().get("/v1/incidents?bbox=1,2,3")
    assert r.status_code == 422
    assert "bbox" in r.json()["detail"].lower()


def test_invalid_bbox_non_numeric():
    r = _client().get("/v1/incidents?bbox=a,b,c,d")
    assert r.status_code == 422
    assert "numbers" in r.json()["detail"].lower()


def test_invalid_bbox_order():
    r = _client().get("/v1/incidents?bbox=10,10,0,0")
    assert r.status_code == 422
    assert "min < max" in r.json()["detail"].lower()


def test_invalid_date_range():
    r = _client().get("/v1/incidents?date_from=2025-01-02&date_to=2025-01-01")
    assert r.status_code == 422
    assert "date_from" in r.json()["detail"].lower()


def test_limit_out_of_range_low():
    r = _client().get("/v1/incidents?limit=0")
    assert r.status_code == 422


def test_limit_out_of_range_high():
    r = _client().get("/v1/incidents?limit=999999")
    assert r.status_code == 422
