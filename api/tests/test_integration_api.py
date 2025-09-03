import os

import pytest
from fastapi.testclient import TestClient

from api.main import app

pytestmark = pytest.mark.integration


PG_DSN = os.getenv("PG_DSN")


@pytest.fixture(autouse=True)
def _require_pg_dsn():
    if not PG_DSN:
        pytest.skip("PG_DSN not set; integration test requires a live Postgres")


def test_health_real_db():
    client = TestClient(app)
    r = client.get("/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True


def test_neighbourhoods_and_incidents_end_to_end():
    client = TestClient(app)

    # Neighbourhood seeded in db/init/003_seed.sql
    rn = client.get("/v1/neighbourhoods?code=001")
    assert rn.status_code == 200
    nb = rn.json()
    assert nb["type"] == "FeatureCollection"
    assert len(nb["features"]) >= 1

    # Incidents within bbox around the seeded point
    ri = client.get("/v1/incidents", params={"dataset": "robbery", "bbox": "-79.6,43.6,-79.3,43.8", "limit": 10})
    assert ri.status_code == 200
    fc = ri.json()
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) >= 1
