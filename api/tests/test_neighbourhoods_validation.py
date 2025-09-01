from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_neighbourhoods_invalid_bbox_format():
    r = client.get("/v1/neighbourhoods?bbox=1,2,3")
    assert r.status_code == 422
    assert "bbox" in r.json()["detail"].lower()


def test_neighbourhoods_invalid_bbox_non_numeric():
    r = client.get("/v1/neighbourhoods?bbox=a,b,c,d")
    assert r.status_code == 422
    assert "numbers" in r.json()["detail"].lower()


def test_neighbourhoods_invalid_bbox_order():
    r = client.get("/v1/neighbourhoods?bbox=10,10,0,0")
    assert r.status_code == 422
    assert "min < max" in r.json()["detail"].lower()
