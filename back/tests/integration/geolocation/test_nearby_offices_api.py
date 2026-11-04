import pytest
from fastapi.testclient import TestClient

from conco.main import app

pytestmark = pytest.mark.integration


def test_nearby_offices_endpoint_against_real_epok() -> None:
    client = TestClient(app)

    response = client.get(
        "/geolocation/nearby-offices",
        params={"latitude": -34.6047137, "longitude": -58.4021372, "limit": 3},
    )

    assert response.status_code == 200
    body = response.json()
    offices = body["offices"]
    assert 1 <= len(offices) <= 3
    distances = [office["distance_meters"] for office in offices]
    assert distances == sorted(distances)
    assert all(office["address"] for office in offices)
    assert "epok.buenosaires.gob.ar" in body["source"]["url"]
