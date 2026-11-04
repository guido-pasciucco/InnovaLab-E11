from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from conco.geolocation.api import get_location_checker
from conco.geolocation.domain import LocationCheck, LocationCheckError, Source
from conco.main import app

URL = "/geolocation/location-check"

SOURCE = Source(
    name="Georef - Servicio de Normalización de Datos Geográficos de Argentina",
    url="https://apis.datos.gob.ar/georef/api",
    license="CC BY 4.0",
)
IN_CABA = LocationCheck(
    in_caba=True, province="Ciudad Autónoma de Buenos Aires", department="Comuna 3"
)

SOURCE_JSON = {
    "name": "Georef - Servicio de Normalización de Datos Geográficos de Argentina",
    "url": "https://apis.datos.gob.ar/georef/api",
    "license": "CC BY 4.0",
}
UNAVAILABLE_JSON = {
    "detail": "El servicio de ubicación no está disponible. Intentá de nuevo más tarde."
}


class FakeLocationChecker:
    """Reemplaza a Georef en los tests: devuelve un resultado fijo y anota cada llamada."""

    def __init__(self) -> None:
        self.result = IN_CABA
        self.error: Exception | None = None
        self.calls: list[tuple[float, float]] = []

    @property
    def source(self) -> Source:
        return SOURCE

    async def check(self, latitude: float, longitude: float) -> LocationCheck:
        self.calls.append((latitude, longitude))
        if self.error is not None:
            raise self.error
        return self.result


@pytest.fixture
def checker() -> FakeLocationChecker:
    return FakeLocationChecker()


@pytest.fixture
def client(checker: FakeLocationChecker) -> Iterator[TestClient]:
    app.dependency_overrides[get_location_checker] = lambda: checker
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_a_point_in_caba_returns_in_caba_true_and_the_source(
    client: TestClient, checker: FakeLocationChecker
) -> None:
    response = client.get(URL, params={"latitude": -34.6047137, "longitude": -58.4021372})

    assert response.status_code == 200
    assert response.json() == {
        "location": {
            "in_caba": True,
            "province": "Ciudad Autónoma de Buenos Aires",
            "department": "Comuna 3",
        },
        "source": SOURCE_JSON,
    }
    assert checker.calls == [(-34.6047137, -58.4021372)]


def test_a_point_outside_caba_returns_200_with_in_caba_false(
    client: TestClient, checker: FakeLocationChecker
) -> None:
    checker.result = LocationCheck(in_caba=False, province="Buenos Aires", department="La Plata")

    response = client.get(URL, params={"latitude": -34.9214, "longitude": -57.9545})

    assert response.status_code == 200
    assert response.json()["location"] == {
        "in_caba": False,
        "province": "Buenos Aires",
        "department": "La Plata",
    }


def test_a_point_outside_argentina_returns_200_with_null_names(
    client: TestClient, checker: FakeLocationChecker
) -> None:
    checker.result = LocationCheck(in_caba=False, province=None, department=None)

    response = client.get(URL, params={"latitude": -40.0, "longitude": -30.0})

    assert response.status_code == 200
    assert response.json()["location"] == {
        "in_caba": False,
        "province": None,
        "department": None,
    }


def test_error_returns_502(client: TestClient, checker: FakeLocationChecker) -> None:
    checker.error = LocationCheckError("Georef no responde")

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
    ],
)
def test_invalid_params_return_422_without_calling_the_checker(
    client: TestClient, checker: FakeLocationChecker, params: dict[str, object]
) -> None:
    response = client.get(URL, params=params)

    assert response.status_code == 422
    assert checker.calls == []


def test_existing_geolocation_routes_are_still_registered(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert "/geolocation/addresses" in paths
    assert "/geolocation/address-context" in paths
    assert "/geolocation/address-context/by-coordinates" in paths
    assert "/geolocation/nearby-offices" in paths
    assert URL in paths
