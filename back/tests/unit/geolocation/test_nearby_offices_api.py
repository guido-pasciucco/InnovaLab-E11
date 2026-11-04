from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from conco.geolocation.api import get_nearby_office_finder
from conco.geolocation.domain import NearbyOffice, NearbyOfficeError, Source
from conco.main import app

URL = "/geolocation/nearby-offices"

SOURCE = Source(
    name="USIG - EPOK (Gobierno de la Ciudad de Buenos Aires)",
    url="https://epok.buenosaires.gob.ar",
    license="CC BY 2.5 AR",
)
SAMPLE_OFFICE = NearbyOffice(
    name="Sede Comunal 2",
    address="URIBURU JOSE E., Pres. 1022",
    phone="4370-9702",
    neighborhood="RECOLETA",
    commune="Comuna 2",
    distance_meters=940.95,
    info_url="https://buenosaires.gob.ar/comuna-2",
    last_updated="2024-04-11",
)

OFFICE_JSON = {
    "name": "Sede Comunal 2",
    "address": "URIBURU JOSE E., Pres. 1022",
    "phone": "4370-9702",
    "neighborhood": "RECOLETA",
    "commune": "Comuna 2",
    "distance_meters": 940.95,
    "info_url": "https://buenosaires.gob.ar/comuna-2",
    "last_updated": "2024-04-11",
}
SOURCE_JSON = {
    "name": "USIG - EPOK (Gobierno de la Ciudad de Buenos Aires)",
    "url": "https://epok.buenosaires.gob.ar",
    "license": "CC BY 2.5 AR",
}
UNAVAILABLE_JSON = {
    "detail": "El servicio de lugares de la Ciudad no está disponible. Intentá de nuevo más tarde."
}


class FakeNearbyOfficeFinder:
    """Reemplaza a EPOK en los tests: devuelve datos fijos y anota cada llamada."""

    def __init__(self) -> None:
        self.offices: list[NearbyOffice] = [SAMPLE_OFFICE]
        self.error: Exception | None = None
        self.calls: list[tuple[float, float, int]] = []

    @property
    def source(self) -> Source:
        return SOURCE

    async def find_nearby(
        self, latitude: float, longitude: float, limit: int
    ) -> list[NearbyOffice]:
        self.calls.append((latitude, longitude, limit))
        if self.error is not None:
            raise self.error
        return self.offices


@pytest.fixture
def finder() -> FakeNearbyOfficeFinder:
    return FakeNearbyOfficeFinder()


@pytest.fixture
def client(finder: FakeNearbyOfficeFinder) -> Iterator[TestClient]:
    app.dependency_overrides[get_nearby_office_finder] = lambda: finder
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_returns_the_offices_and_their_source(
    client: TestClient, finder: FakeNearbyOfficeFinder
) -> None:
    response = client.get(URL, params={"latitude": -34.6047137, "longitude": -58.4021372})

    assert response.status_code == 200
    assert response.json() == {"offices": [OFFICE_JSON], "source": SOURCE_JSON}
    assert finder.calls == [(-34.6047137, -58.4021372, 3)]


def test_passes_the_requested_limit(client: TestClient, finder: FakeNearbyOfficeFinder) -> None:
    client.get(URL, params={"latitude": -34.6, "longitude": -58.4, "limit": 5})

    assert finder.calls == [(-34.6, -58.4, 5)]


def test_optional_fields_can_be_null(
    client: TestClient, finder: FakeNearbyOfficeFinder
) -> None:
    finder.offices = [
        SAMPLE_OFFICE.model_copy(
            update={
                "phone": None,
                "neighborhood": None,
                "commune": None,
                "info_url": None,
                "last_updated": None,
            }
        )
    ]

    response = client.get(URL, params={"latitude": -34.6, "longitude": -58.4})

    assert response.status_code == 200
    assert response.json()["offices"] == [
        {
            **OFFICE_JSON,
            "phone": None,
            "neighborhood": None,
            "commune": None,
            "info_url": None,
            "last_updated": None,
        }
    ]


def test_nothing_in_range_returns_200_with_an_empty_list(
    client: TestClient, finder: FakeNearbyOfficeFinder
) -> None:
    finder.offices = []

    response = client.get(URL, params={"latitude": -34.6423652, "longitude": -58.7567541})

    assert response.status_code == 200
    assert response.json() == {"offices": [], "source": SOURCE_JSON}


def test_error_returns_502(client: TestClient, finder: FakeNearbyOfficeFinder) -> None:
    finder.error = NearbyOfficeError("EPOK no responde")

    response = client.get(URL, params={"latitude": -34.6, "longitude": -58.4})

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
        {"latitude": -34.6, "longitude": -58.4, "limit": 0},
        {"latitude": -34.6, "longitude": -58.4, "limit": 6},
        {"latitude": -34.6, "longitude": -58.4, "limit": "tres"},
    ],
)
def test_invalid_params_return_422_without_calling_the_finder(
    client: TestClient, finder: FakeNearbyOfficeFinder, params: dict[str, object]
) -> None:
    response = client.get(URL, params=params)

    assert response.status_code == 422
    assert finder.calls == []


def test_existing_geolocation_routes_are_still_registered(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert "/geolocation/addresses" in paths
    assert "/geolocation/address-context" in paths
    assert "/geolocation/address-context/by-coordinates" in paths
    assert URL in paths
