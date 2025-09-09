import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from api.main import app

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


def test_health_inmemory_db():
    """Integration test using mocked ping (in-memory)."""
    async def mock_ping():
        return True

    with patch("api.routers.health.ping", side_effect=mock_ping):
        client = TestClient(app)
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True


def test_incidents_inmemory_db():
    """Integration test with mocked incidents cursor."""
    def mock_cursor():
        cur = AsyncMock()
        # Default return values for any execute
        cur.fetchall.return_value = [
            {
                "id": 1,
                "dataset": "robbery",
                "event_unique_id": "E1",
                "report_date": "2024-01-01T00:00:00Z",
                "occ_date": "2024-01-01T00:00:00Z",
                "offence": "Robbery",
                "mci_category": "Robbery",
                "hood_158": "001",
                "lon": -79.4,
                "lat": 43.7,
                "geometry": {"type": "Point", "coordinates": [-79.4, 43.7]},
            }
        ]
        cur.fetchone.return_value = {"total": 1, "c": 1}
        cur.__aenter__ = AsyncMock(return_value=cur)
        cur.__aexit__ = AsyncMock(return_value=None)
        return cur

    with patch("api.routers.incidents.cursor", mock_cursor):
        client = TestClient(app)
        r = client.get("/v1/incidents?limit=1")
        assert r.status_code == 200
        data = r.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) >= 1


def test_neighbourhoods_inmemory_db():
    """Integration test with mocked neighbourhoods cursor."""
    def mock_cursor():
        cur = AsyncMock()
        cur.fetchall.return_value = [
            {
                "area_long_code": "001",
                "area_short_code": "1",
                "area_name": "Downtown",
                "geometry": {"type": "Polygon", "coordinates": [[[0,0],[1,0],[1,1],[0,1],[0,0]]]},
            }
        ]
        cur.fetchone.return_value = {"total": 1}
        cur.__aenter__ = AsyncMock(return_value=cur)
        cur.__aexit__ = AsyncMock(return_value=None)
        return cur

    with patch("api.routers.neighbourhoods.cursor", mock_cursor):
        client = TestClient(app)
        r = client.get("/v1/neighbourhoods")
        assert r.status_code == 200
        data = r.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) >= 1


def test_neighbourhoods_and_incidents_end_to_end_inmemory():
    """End-to-end flow using mocked neighbourhoods and incidents cursors."""
    def mock_incidents_cursor():
        cur = AsyncMock()
        cur.fetchall.return_value = [
            {
                "id": 1,
                "dataset": "robbery",
                "event_unique_id": "E1",
                "report_date": "2024-01-01T00:00:00Z",
                "occ_date": "2024-01-01T00:00:00Z",
                "offence": "Robbery",
                "mci_category": "Robbery",
                "hood_158": "001",
                "lon": -79.4,
                "lat": 43.7,
                "geometry": {"type": "Point", "coordinates": [-79.4, 43.7]},
            }
        ]
        cur.fetchone.return_value = {"total": 1, "c": 1}
        cur.__aenter__ = AsyncMock(return_value=cur)
        cur.__aexit__ = AsyncMock(return_value=None)
        return cur

    def mock_neighbourhoods_cursor():
        cur = AsyncMock()
        cur.fetchall.return_value = [
            {
                "area_long_code": "001",
                "area_short_code": "1",
                "area_name": "Downtown",
                "geometry": {"type": "Polygon", "coordinates": [[[0,0],[1,0],[1,1],[0,1],[0,0]]]},
            }
        ]
        cur.fetchone.return_value = {"total": 1}
        cur.__aenter__ = AsyncMock(return_value=cur)
        cur.__aexit__ = AsyncMock(return_value=None)
        return cur

    with patch("api.routers.neighbourhoods.cursor", mock_neighbourhoods_cursor), \
         patch("api.routers.incidents.cursor", mock_incidents_cursor):
        client = TestClient(app)

        rn = client.get("/v1/neighbourhoods?code=001")
        assert rn.status_code == 200
        nb = rn.json()
        assert nb["type"] == "FeatureCollection"
        assert len(nb["features"]) >= 1

        ri = client.get("/v1/incidents", params={"dataset": "robbery", "bbox": "-79.6,43.6,-79.3,43.8", "limit": 10})
        assert ri.status_code == 200
        fc = ri.json()
        assert fc["type"] == "FeatureCollection"
        assert len(fc["features"]) >= 1
