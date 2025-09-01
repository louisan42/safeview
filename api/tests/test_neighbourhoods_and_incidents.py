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


def test_neighbourhoods_geojson(monkeypatch):
    rows = [
        {
            "area_long_code": "001",
            "area_short_code": "1",
            "area_name": "Test Region",
            "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
        }
    ]
    monkeypatch.setattr(nbhd, "cursor", lambda: _fake_cursor_cm_nbhd(rows))

    client = TestClient(app)
    r = client.get("/v1/neighbourhoods")
    assert r.status_code == 200
    body = r.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 1
    f = body["features"][0]
    assert f["type"] == "Feature"
    assert f["geometry"]["type"] == "Polygon"
    assert f["properties"]["area_long_code"] == "001"


def test_incidents_geojson(monkeypatch):
    inc_rows = [
        {
            "id": 123,
            "dataset": "robbery",
            "event_unique_id": "E1",
            "report_date": "2025-01-01T00:00:00Z",
            "occ_date": "2025-01-01T00:00:00Z",
            "offence": "Robbery",
            "mci_category": "Robbery",
            "hood_158": "001",
            "lon": -79.4,
            "lat": 43.7,
            "geometry": None,
        }
    ]
    geom_rows = [
        {"id": 123, "geometry": {"type": "Point", "coordinates": [-79.4, 43.7]}}
    ]

    monkeypatch.setattr(inc, "cursor", lambda: _fake_cursor_cm_inc(inc_rows, geom_rows))

    client = TestClient(app)
    r = client.get("/v1/incidents?dataset=robbery&limit=1")
    assert r.status_code == 200
    body = r.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 1
    f = body["features"][0]
    assert f["geometry"]["type"] == "Point"
    assert f["properties"]["dataset"] == "robbery"
    assert f["properties"]["id"] == 123
