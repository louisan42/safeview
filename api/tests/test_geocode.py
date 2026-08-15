from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app


class TestGeocode:
    def test_geocode_maps_nominatim_hits(self):
        payload = [
            {"display_name": "City Hall, Toronto", "lat": "43.6532", "lon": "-79.3832"},
        ]
        with patch("api.routers.geocode._nominatim_search", return_value=payload):
            client = TestClient(app)
            response = client.get("/v1/geocode?q=city%20hall")
        assert response.status_code == 200
        body = response.json()
        assert len(body["results"]) == 1
        assert body["results"][0]["lat"] == 43.6532
        assert body["results"][0]["lng"] == -79.3832
        assert "Toronto" in body["results"][0]["label"]
