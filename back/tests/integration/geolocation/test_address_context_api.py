import pytest
from fastapi.testclient import TestClient

from conco.main import app

pytestmark = pytest.mark.integration


def test_address_context_endpoints_against_real_usig() -> None:
    client = TestClient(app)

    by_address = client.get(
        "/geolocation/address-context", params={"street": "Corrientes", "number": 2500}
    )

    assert by_address.status_code == 200
    body = by_address.json()
    assert body["context"]["commune"] == "Comuna 3"
    assert body["context"]["neighborhood"] == "Balvanera"
    assert body["context"]["postal_code"]
    assert "usig.buenosaires.gob.ar" in body["source"]["url"]

    by_coordinates = client.get(
        "/geolocation/address-context/by-coordinates",
        params={"latitude": -34.604792, "longitude": -58.401981},
    )

    assert by_coordinates.status_code == 200
    assert by_coordinates.json()["context"]["neighborhood"] == "Balvanera"


def test_point_outside_caba_against_real_usig_returns_404() -> None:
    client = TestClient(app)

    response = client.get(
        "/geolocation/address-context/by-coordinates",
        params={"latitude": -34.6423652, "longitude": -58.7567541},
    )

    assert response.status_code == 404
