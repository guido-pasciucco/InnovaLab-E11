from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from conco.geolocation.api import get_address_finder
from conco.geolocation.domain import Address, AddressSearchError, Coordinates
from conco.main import app

URL = "/geolocation/addresses"

SAMPLE_ADDRESS = Address(
    full_address="AV CORRIENTES 2500, Comuna 3, Ciudad Autónoma de Buenos Aires",
    street="AV CORRIENTES",
    number=2500,
    department="Comuna 3",
    locality="Ciudad Autónoma de Buenos Aires",
    province="Ciudad Autónoma de Buenos Aires",
    coordinates=Coordinates(latitude=-34.6047, longitude=-58.4021),
)


class FakeAddressFinder:
    """Reemplaza a Georef en los tests: devuelve datos fijos y anota cada llamada."""

    def __init__(
        self,
        addresses: list[Address] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.addresses = addresses or []
        self.error = error
        self.calls: list[tuple[str, str, int]] = []

    async def search(self, address: str, province: str, limit: int) -> list[Address]:
        self.calls.append((address, province, limit))
        if self.error is not None:
            raise self.error
        return self.addresses


@pytest.fixture
def finder() -> FakeAddressFinder:
    return FakeAddressFinder(addresses=[SAMPLE_ADDRESS])


@pytest.fixture
def client(finder: FakeAddressFinder) -> Iterator[TestClient]:
    app.dependency_overrides[get_address_finder] = lambda: finder
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_returns_the_addresses_found(client: TestClient) -> None:
    response = client.get(URL, params={"address": "Corrientes 2500"})

    assert response.status_code == 200
    assert response.json() == {
        "addresses": [
            {
                "full_address": "AV CORRIENTES 2500, Comuna 3, Ciudad Autónoma de Buenos Aires",
                "street": "AV CORRIENTES",
                "number": 2500,
                "department": "Comuna 3",
                "locality": "Ciudad Autónoma de Buenos Aires",
                "province": "Ciudad Autónoma de Buenos Aires",
                "coordinates": {"latitude": -34.6047, "longitude": -58.4021},
            }
        ]
    }


def test_uses_caba_and_five_results_by_default(
    client: TestClient, finder: FakeAddressFinder
) -> None:
    client.get(URL, params={"address": "Corrientes 2500"})

    assert finder.calls == [("Corrientes 2500", "caba", 5)]


def test_forwards_province_and_limit(
    client: TestClient, finder: FakeAddressFinder
) -> None:
    client.get(URL, params={"address": "San Martín 100", "province": "cordoba", "limit": 3})

    assert finder.calls == [("San Martín 100", "cordoba", 3)]


def test_no_results_returns_empty_list(client: TestClient, finder: FakeAddressFinder) -> None:
    finder.addresses = []

    response = client.get(URL, params={"address": "Calle Inventada 9999"})

    assert response.status_code == 200
    assert response.json() == {"addresses": []}


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"address": "ab"},
        {"address": "   "},
        {"address": "Corrientes 2500", "limit": 0},
        {"address": "Corrientes 2500", "limit": 11},
    ],
)
def test_invalid_query_returns_422_without_calling_the_finder(
    client: TestClient, finder: FakeAddressFinder, params: dict[str, object]
) -> None:
    response = client.get(URL, params=params)

    assert response.status_code == 422
    assert finder.calls == []


def test_search_error_returns_502(client: TestClient, finder: FakeAddressFinder) -> None:
    finder.error = AddressSearchError("Georef no responde")

    response = client.get(URL, params={"address": "Corrientes 2500"})

    assert response.status_code == 502
    assert response.json() == {
        "detail": "El servicio de direcciones no está disponible. Intentá de nuevo más tarde."
    }
