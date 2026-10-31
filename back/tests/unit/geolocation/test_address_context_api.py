from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from conco.geolocation.api import get_address_context_provider
from conco.geolocation.domain import AddressContext, AddressContextError, Source
from conco.main import app

URL = "/geolocation/address-context"
BY_COORDINATES_URL = f"{URL}/by-coordinates"

SOURCE = Source(
    name="USIG - Datos útiles (Gobierno de la Ciudad de Buenos Aires)",
    url="http://usig.buenosaires.gob.ar/apis/",
    license="Creative Commons Reconocimiento 2.5 Argentina (CC BY 2.5 AR)",
)
SAMPLE_CONTEXT = AddressContext(
    neighborhood="Balvanera",
    commune="Comuna 3",
    postal_code="1046",
    argentine_postal_code="C1046AAP",
)

CONTEXT_JSON = {
    "neighborhood": "Balvanera",
    "commune": "Comuna 3",
    "postal_code": "1046",
    "argentine_postal_code": "C1046AAP",
}
SOURCE_JSON = {
    "name": "USIG - Datos útiles (Gobierno de la Ciudad de Buenos Aires)",
    "url": "http://usig.buenosaires.gob.ar/apis/",
    "license": "Creative Commons Reconocimiento 2.5 Argentina (CC BY 2.5 AR)",
}
NOT_FOUND_JSON = {
    "detail": "No se encontró la ubicación dentro de la Ciudad de Buenos Aires."
}
UNAVAILABLE_JSON = {
    "detail": "El servicio de datos de la Ciudad no está disponible. Intentá de nuevo más tarde."
}


class FakeAddressContextProvider:
    """Reemplaza a USIG en los tests: devuelve datos fijos y anota cada llamada."""

    def __init__(self) -> None:
        self.context: AddressContext | None = SAMPLE_CONTEXT
        self.error: Exception | None = None
        self.address_calls: list[tuple[str, int]] = []
        self.coordinates_calls: list[tuple[float, float]] = []

    @property
    def source(self) -> Source:
        return SOURCE

    async def by_address(self, street: str, number: int) -> AddressContext | None:
        self.address_calls.append((street, number))
        if self.error is not None:
            raise self.error
        return self.context

    async def by_coordinates(self, latitude: float, longitude: float) -> AddressContext | None:
        self.coordinates_calls.append((latitude, longitude))
        if self.error is not None:
            raise self.error
        return self.context


@pytest.fixture
def provider() -> FakeAddressContextProvider:
    return FakeAddressContextProvider()


@pytest.fixture
def client(provider: FakeAddressContextProvider) -> Iterator[TestClient]:
    app.dependency_overrides[get_address_context_provider] = lambda: provider
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_by_address_returns_the_context_and_its_source(
    client: TestClient, provider: FakeAddressContextProvider
) -> None:
    response = client.get(URL, params={"street": "Corrientes", "number": 2500})

    assert response.status_code == 200
    assert response.json() == {"context": CONTEXT_JSON, "source": SOURCE_JSON}
    assert provider.address_calls == [("Corrientes", 2500)]


def test_by_address_not_found_returns_404(
    client: TestClient, provider: FakeAddressContextProvider
) -> None:
    provider.context = None

    response = client.get(URL, params={"street": "Calle Inexistente", "number": 1234})

    assert response.status_code == 404
    assert response.json() == NOT_FOUND_JSON


def test_by_address_error_returns_502(
    client: TestClient, provider: FakeAddressContextProvider
) -> None:
    provider.error = AddressContextError("USIG no responde")

    response = client.get(URL, params={"street": "Corrientes", "number": 2500})

    assert response.status_code == 502
    assert response.json() == UNAVAILABLE_JSON


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"street": "Corrientes"},
        {"number": 2500},
        {"street": "C", "number": 2500},
        {"street": "   ", "number": 2500},
        {"street": "a" * 101, "number": 2500},
        {"street": "Corrientes", "number": 0},
        {"street": "Corrientes", "number": 100000},
        {"street": "Corrientes", "number": "dos mil"},
    ],
)
def test_by_address_invalid_params_return_422_without_calling_the_provider(
    client: TestClient, provider: FakeAddressContextProvider, params: dict[str, object]
) -> None:
    response = client.get(URL, params=params)

    assert response.status_code == 422
    assert provider.address_calls == []


def test_by_coordinates_returns_the_context_and_its_source(
    client: TestClient, provider: FakeAddressContextProvider
) -> None:
    provider.context = SAMPLE_CONTEXT.model_copy(
        update={"postal_code": None, "argentine_postal_code": None}
    )

    response = client.get(
        BY_COORDINATES_URL, params={"latitude": -34.604792, "longitude": -58.401981}
    )

    assert response.status_code == 200
    assert response.json() == {
        "context": {**CONTEXT_JSON, "postal_code": None, "argentine_postal_code": None},
        "source": SOURCE_JSON,
    }
    assert provider.coordinates_calls == [(-34.604792, -58.401981)]


def test_by_coordinates_outside_caba_returns_404(
    client: TestClient, provider: FakeAddressContextProvider
) -> None:
    provider.context = None

    response = client.get(
        BY_COORDINATES_URL, params={"latitude": -34.6423652, "longitude": -58.7567541}
    )

    assert response.status_code == 404
    assert response.json() == NOT_FOUND_JSON


def test_by_coordinates_error_returns_502(
    client: TestClient, provider: FakeAddressContextProvider
) -> None:
    provider.error = AddressContextError("USIG no responde")

    response = client.get(
        BY_COORDINATES_URL, params={"latitude": -34.604792, "longitude": -58.401981}
    )

    assert response.status_code == 502
    assert response.json() == UNAVAILABLE_JSON


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"latitude": -34.6},
        {"longitude": -58.4},
        {"latitude": -90.1, "longitude": -58.4},
        {"latitude": 90.1, "longitude": -58.4},
        {"latitude": -34.6, "longitude": -180.1},
        {"latitude": -34.6, "longitude": 180.1},
        {"latitude": "norte", "longitude": -58.4},
    ],
)
def test_by_coordinates_invalid_params_return_422_without_calling_the_provider(
    client: TestClient, provider: FakeAddressContextProvider, params: dict[str, object]
) -> None:
    response = client.get(BY_COORDINATES_URL, params=params)

    assert response.status_code == 422
    assert provider.coordinates_calls == []


def test_existing_address_search_route_is_still_registered(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert "/geolocation/addresses" in paths
    assert URL in paths
    assert BY_COORDINATES_URL in paths
