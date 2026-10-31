import pytest
from fastapi.testclient import TestClient

from conco.main import app

pytestmark = pytest.mark.integration


def test_search_addresses_endpoint_against_real_georef() -> None:
    client = TestClient(app)

    response = client.get(
        "/geolocation/addresses", params={"address": "Corrientes 2500"}
    )

    assert response.status_code == 200
    address = response.json()["addresses"][0]
    assert "CORRIENTES 2500" in address["full_address"]
    assert address["department"] == "Comuna 3"
    assert -34.7 <= address["coordinates"]["latitude"] <= -34.5
    assert -58.5 <= address["coordinates"]["longitude"] <= -58.3
