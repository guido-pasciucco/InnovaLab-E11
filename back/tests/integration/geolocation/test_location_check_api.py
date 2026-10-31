import pytest
from fastapi.testclient import TestClient

from conco.main import app

pytestmark = pytest.mark.integration


def test_location_check_endpoint_against_real_georef() -> None:
    client = TestClient(app)

    in_caba = client.get(
        "/geolocation/location-check",
        params={"latitude": -34.6047137, "longitude": -58.4021372},
    )
    la_plata = client.get(
        "/geolocation/location-check",
        params={"latitude": -34.9214, "longitude": -57.9545},
    )

    assert in_caba.status_code == 200
    assert in_caba.json()["location"] == {
        "in_caba": True,
        "province": "Ciudad Autónoma de Buenos Aires",
        "department": "Comuna 3",
    }
    assert "georef" in in_caba.json()["source"]["url"]
    assert la_plata.status_code == 200
    assert la_plata.json()["location"]["in_caba"] is False
