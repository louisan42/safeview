from fastapi.testclient import TestClient

import api.routers.neighbourhoods as nbhd
import api.routers.incidents as inc
from api.main import app


class _FakeCursor:
    def __init__(self, rows_nbhd=None, rows_incidents=None, rows_geom=None):
        self._rows_nbhd = rows_nbhd or []
        self._rows_incidents = rows_incidents or []
        self._rows_geom = rows_geom or []
        self._last_sql = ""
        self._last_params = None

    async def execute(self, sql, params=None):
        self._last_sql = sql
        self._last_params = params

    async def fetchall(self):
        if "json_build_object" in self._last_sql:
            return self._rows_geom
        if "FROM cot_neighbourhoods_158" in self._last_sql:
            return self._rows_nbhd
        return self._rows_incidents

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

class _FakeCursorCM:
    def __init__(self, rows_nbhd=None, rows_incidents=None, rows_geom=None):
        self._rows_nbhd = rows_nbhd
        self._rows_incidents = rows_incidents
        self._rows_geom = rows_geom

    async def __aenter__(self):
        return _FakeCursor(
            rows_nbhd=self._rows_nbhd,
            rows_incidents=self._rows_incidents,
            rows_geom=self._rows_geom,
        )

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _fake_cursor_cm_nbhd(rows):
    return _FakeCursorCM(rows_nbhd=rows)


def _fake_cursor_cm_inc(rows_incidents, rows_geom):
    return _FakeCursorCM(rows_incidents=rows_incidents, rows_geom=rows_geom)


def test_neighbourhoods_geojson():
    """Test neighbourhoods endpoint returns valid GeoJSON"""
    client = TestClient(app)
    r = client.get("/v1/neighbourhoods")
    assert r.status_code == 200
    body = r.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) > 0  # Should have neighbourhoods
    f = body["features"][0]
    assert f["type"] == "Feature"
    assert f["geometry"]["type"] == "Polygon"
    assert "area_long_code" in f["properties"]


def test_incidents_geojson():
    """Test incidents endpoint returns valid GeoJSON"""
    client = TestClient(app)
    r = client.get("/v1/incidents?limit=1")
    assert r.status_code == 200
    body = r.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) > 0  # Should have incidents
    f = body["features"][0]
    assert f["geometry"]["type"] == "Point"
    assert "dataset" in f["properties"]
    assert "id" in f["properties"]
