import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import respx
from fastapi.testclient import TestClient

from conco.config import settings
from conco.geolocation.api import get_address_finder
from conco.geolocation.domain import Address, Coordinates
from conco.main import app
from conco.territory.api import get_references_resolver, get_use_table_resolver
from conco.territory.domain import (
    APPROXIMATE_LOCATION_LIMITATION,
    SOURCE,
    Category,
    Rubro,
    RubroReferences,
    TerritoryLookupError,
    UseTable,
)

USE_TABLE_URL = "/territory/use-table"
REFERENCIAS_URL = "/territory/rubro-referencias"
PARCEL_GEOMETRY_URL = "/territory/parcel-geometry"

EXPECTED_SOURCE = {
    "id": "usig-ciudad-3d",
    "title": "Ciudad 3D — Cuadro de usos",
    "publisher": "USIG, Gobierno de la Ciudad de Buenos Aires",
    "url": "https://ciudad3d.buenosaires.gob.ar",
}
LIMITATIONS = [
    APPROXIMATE_LOCATION_LIMITATION,
    "Información de referencia del cuadro de usos oficial: no acredita la zonificación del lote ni confirma que una actividad esté permitida.",
]
NO_PARCELA_LIMITATION = "No se encontró la parcela para el punto consultado dentro de la Ciudad Autónoma de Buenos Aires."

SAMPLE_USE_TABLE = UseTable(
    smp="013-099-018",
    official_address="CORRIENTES AV. 2801",
    mix_area=4,
    categories=[
        Category(
            id=1,
            name="Comercial",
            rubros=[
                Rubro(
                    id=102,
                    name="1.5. Alimentación en general y gastronomía",
                )
            ],
        )
    ],
    source=SOURCE,
    limitations=LIMITATIONS,
)

SAMPLE_REFERENCES = RubroReferences(
    permitido_mixtura_de_usos=["Permitido en el Área de Mixtura de Usos"],
    bicicletas=["Salón de 150m² o más: 30%, como mínimo."],
    estacionamientos=["Salón de 150m2 o más: 20%, como mínimo."],
    cargaydescarga=["No tiene requerimiento"],
    observaciones="Ver art. 3.6.1.1",
    source=SAMPLE_USE_TABLE.source,
    limitations=LIMITATIONS,
)


class FakeResolver:
    """Reemplaza al puerto de territorio: devuelve un resultado o lanza un error."""

    def __init__(self, result: object) -> None:
        self.result = result
        self.calls: list[tuple[object, ...]] = []

    async def resolve(self, *args: object) -> object:
        self.calls.append(args)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class FakeAddressFinder:
    """Reemplaza a Georef para probar que la ruta existente sigue igual."""

    async def search(self, address: str, province: str, limit: int) -> list[Address]:
        return [
            Address(
                full_address="AV CORRIENTES 2500, CABA",
                street="AV CORRIENTES",
                number=2500,
                department="Comuna 3",
                locality="CABA",
                province="CABA",
                coordinates=Coordinates(latitude=-34.6047, longitude=-58.4021),
            )
        ]


@pytest.fixture
def use_table_resolver() -> FakeResolver:
    return FakeResolver(SAMPLE_USE_TABLE)


@pytest.fixture
def references_resolver() -> FakeResolver:
    return FakeResolver(SAMPLE_REFERENCES)


@pytest.fixture
def client(
    use_table_resolver: FakeResolver, references_resolver: FakeResolver
) -> Iterator[TestClient]:
    app.dependency_overrides[get_use_table_resolver] = lambda: use_table_resolver
    app.dependency_overrides[get_references_resolver] = lambda: references_resolver
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_use_table_returns_the_exact_public_contract(client: TestClient) -> None:
    response = client.get(
        USE_TABLE_URL, params={"lat": -34.6040, "lng": -58.4055}
    )

    assert response.status_code == 200
    assert response.json() == {
        "smp": "013-099-018",
        "official_address": "CORRIENTES AV. 2801",
        "mix_area": 4,
        "categories": [
            {
                "id": 1,
                "name": "Comercial",
                "rubros": [
                    {"id": 102, "name": "1.5. Alimentación en general y gastronomía"}
                ],
            }
        ],
        "source": EXPECTED_SOURCE,
        "limitations": LIMITATIONS,
    }


def test_use_table_forwards_coordinates(
    client: TestClient, use_table_resolver: FakeResolver
) -> None:
    client.get(USE_TABLE_URL, params={"lat": -34.6040, "lng": -58.4055})

    assert use_table_resolver.calls == [(-34.6040, -58.4055)]


def test_empty_parcela_returns_null_smp_and_empty_categories(
    client: TestClient, use_table_resolver: FakeResolver
) -> None:
    use_table_resolver.result = UseTable(
        smp=None,
        official_address=None,
        mix_area=None,
        categories=[],
        source=SAMPLE_USE_TABLE.source,
        limitations=[NO_PARCELA_LIMITATION] + LIMITATIONS,
    )

    response = client.get(USE_TABLE_URL, params={"lat": -34.5, "lng": -58.4})

    assert response.status_code == 200
    body = response.json()
    assert body["smp"] is None
    assert body["official_address"] is None
    assert body["mix_area"] is None
    assert body["categories"] == []
    assert NO_PARCELA_LIMITATION in body["limitations"]
    assert APPROXIMATE_LOCATION_LIMITATION in body["limitations"]


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"lng": -58.4055},
        {"lat": -34.6040},
        {"lat": 91, "lng": -58.4055},
        {"lat": -34.6040, "lng": 181},
    ],
)
def test_invalid_coordinates_return_422_without_resolving(
    client: TestClient,
    use_table_resolver: FakeResolver,
    params: dict[str, object],
) -> None:
    response = client.get(USE_TABLE_URL, params=params)

    assert response.status_code == 422
    assert use_table_resolver.calls == []


def test_use_table_upstream_failure_returns_503_with_standard_body(
    client: TestClient, use_table_resolver: FakeResolver
) -> None:
    use_table_resolver.result = TerritoryLookupError("USIG no responde")

    response = client.get(USE_TABLE_URL, params={"lat": -34.6040, "lng": -58.4055})

    assert response.status_code == 503
    assert response.json() == {
        "code": "TERRITORY_UNAVAILABLE",
        "request_id": response.headers["x-request-id"],
        "detail": "No pudimos consultar el cuadro de usos. Intentá de nuevo más tarde.",
    }


def test_rubro_referencias_returns_the_exact_public_contract(client: TestClient) -> None:
    response = client.get(
        REFERENCIAS_URL,
        params={"smp": "013-099-018", "categoria": 1, "mixtura": 4, "rubro": 102},
    )

    assert response.status_code == 200
    assert response.json() == {
        "permitido_mixtura_de_usos": ["Permitido en el Área de Mixtura de Usos"],
        "bicicletas": ["Salón de 150m² o más: 30%, como mínimo."],
        "estacionamientos": ["Salón de 150m2 o más: 20%, como mínimo."],
        "cargaydescarga": ["No tiene requerimiento"],
        "observaciones": "Ver art. 3.6.1.1",
        "source": EXPECTED_SOURCE,
        "limitations": LIMITATIONS,
    }


def test_rubro_referencias_observaciones_can_be_null(
    client: TestClient, references_resolver: FakeResolver
) -> None:
    references_resolver.result = RubroReferences(
        permitido_mixtura_de_usos=[],
        bicicletas=[],
        estacionamientos=[],
        cargaydescarga=[],
        observaciones=None,
        source=SOURCE,
        limitations=LIMITATIONS,
    )

    response = client.get(
        REFERENCIAS_URL,
        params={"smp": "013-099-018", "categoria": 1, "mixtura": 4, "rubro": 102},
    )

    assert response.status_code == 200
    assert response.json()["observaciones"] is None


@pytest.mark.parametrize(
    "params",
    [
        {"categoria": 1, "mixtura": 4, "rubro": 102},
        {"smp": "", "categoria": 1, "mixtura": 4, "rubro": 102},
        {"smp": "013-099-018", "categoria": 0, "mixtura": 4, "rubro": 102},
        {"smp": "013-099-018", "categoria": 11, "mixtura": 4, "rubro": 102},
        {"smp": "013-099-018", "categoria": 1, "mixtura": -1, "rubro": 102},
        {"smp": "013-099-018", "categoria": 1, "mixtura": 4, "rubro": 0},
    ],
)
def test_invalid_referencias_params_return_422_without_resolving(
    client: TestClient,
    references_resolver: FakeResolver,
    params: dict[str, object],
) -> None:
    response = client.get(REFERENCIAS_URL, params=params)

    assert response.status_code == 422
    assert references_resolver.calls == []


def test_rubro_referencias_upstream_failure_returns_503(
    client: TestClient, references_resolver: FakeResolver
) -> None:
    references_resolver.result = TerritoryLookupError("USIG no responde")

    response = client.get(
        REFERENCIAS_URL,
        params={"smp": "013-099-018", "categoria": 1, "mixtura": 4, "rubro": 102},
    )

    assert response.status_code == 503
    assert response.json()["code"] == "TERRITORY_UNAVAILABLE"


def test_existing_geolocation_addresses_behavior_is_unchanged() -> None:
    app.dependency_overrides[get_address_finder] = lambda: FakeAddressFinder()
    try:
        response = TestClient(app).get(
            "/geolocation/addresses", params={"address": "Corrientes 2500"}
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["addresses"][0]["full_address"] == "AV CORRIENTES 2500, CABA"


# Los tests de arriba inyectan fakes con `resolve()`. Estos dos ejercitan la
# inyección real: sin ellos, un cambio de nombre en el adaptador pasa los tests
# y el endpoint responde 500 en producción.
FIXTURES_DIR = Path(__file__).parents[2] / "fixtures" / "usig"
BASE = settings.usig_base_url


def load_fixture(name: str) -> Any:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


@respx.mock
def test_real_use_table_resolver_is_wired_to_the_port() -> None:
    respx.get(f"{BASE}/catastro/parcela/").respond(
        200, json=load_fixture("parcela_corrientes.json")
    )
    respx.get(f"{BASE}/cur3d/mixtura_usos/").respond(
        200, json=load_fixture("mixtura_usos.json")
    )
    respx.get(f"{BASE}/cur3d/categorias/").respond(
        200, json=load_fixture("categorias.json")
    )
    respx.get(f"{BASE}/cur3d/cuadrosdeuso/rubros/").respond(
        200, json=load_fixture("rubros.json")
    )

    response = TestClient(app).get(USE_TABLE_URL, params={"lat": -34.6040, "lng": -58.4055})

    assert response.status_code == 200
    assert response.json()["smp"] == "013-099-018"
    assert len(response.json()["categories"]) == 10


@respx.mock
def test_real_references_resolver_is_wired_to_the_port() -> None:
    respx.get(f"{BASE}/cur3d/mixtura_usos/").respond(
        200, json=load_fixture("mixtura_usos.json")
    )
    respx.get(f"{BASE}/cur3d/cuadrosdeuso/referencias/").respond(
        200, json=load_fixture("referencias.json")
    )

    response = TestClient(app).get(
        REFERENCIAS_URL,
        params={"smp": "013-099-018", "categoria": 1, "mixtura": 4, "rubro": 102},
    )

    assert response.status_code == 200
    assert response.json()["permitido_mixtura_de_usos"]


@respx.mock
def test_rubro_referencias_uses_the_mix_area_derived_from_smp() -> None:
    """S11: `mixtura` se acepta por contrato, pero USIG recibe la derivada del SMP."""
    respx.get(f"{BASE}/cur3d/mixtura_usos/").respond(
        200, json=load_fixture("mixtura_usos.json")
    )
    referencias = respx.get(f"{BASE}/cur3d/cuadrosdeuso/referencias/").respond(
        200, json=load_fixture("referencias.json")
    )

    response = TestClient(app).get(
        REFERENCIAS_URL,
        params={"smp": "013-099-018", "categoria": 1, "mixtura": 9, "rubro": 102},
    )

    assert response.status_code == 200
    assert referencias.calls.last.request.url.params["mixtura"] == "4"


@respx.mock
def test_parcel_geometry_returns_a_real_multipolygon_through_real_di() -> None:
    """S12: sin dependency_overrides, la DI real debe exponer la geometría de USIG."""
    respx.get(f"{BASE}/catastro/geometria/").respond(
        200, json=load_fixture("geometria.json")
    )

    response = TestClient(app).get(
        PARCEL_GEOMETRY_URL, params={"smp": "013-099-018"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["geometry"]["type"] == "MultiPolygon"
    assert body["source"] == EXPECTED_SOURCE
    assert APPROXIMATE_LOCATION_LIMITATION in body["limitations"]
    assert any("referencia" in item.lower() for item in body["limitations"])


@respx.mock
def test_parcel_geometry_without_features_returns_null_geometry() -> None:
    respx.get(f"{BASE}/catastro/geometria/").respond(
        200, json={"type": "FeatureCollection", "features": []}
    )

    response = TestClient(app).get(
        PARCEL_GEOMETRY_URL, params={"smp": "000-000-000"}
    )

    assert response.status_code == 200
    assert response.json()["geometry"] is None


@pytest.mark.parametrize("params", [{}, {"smp": ""}])
def test_invalid_parcel_geometry_params_return_422(params: dict[str, object]) -> None:
    assert TestClient(app).get(PARCEL_GEOMETRY_URL, params=params).status_code == 422


@respx.mock
def test_parcel_geometry_upstream_failure_keeps_the_standard_error_body() -> None:
    respx.get(f"{BASE}/catastro/geometria/").respond(500, text="down")

    response = TestClient(app).get(
        PARCEL_GEOMETRY_URL, params={"smp": "013-099-018"}
    )

    assert response.status_code == 503
    assert response.json() == {
        "code": "TERRITORY_UNAVAILABLE",
        "request_id": response.headers["x-request-id"],
        "detail": "No pudimos consultar el cuadro de usos. Intentá de nuevo más tarde.",
    }


# S14: el parámetro opcional `address` llega al puerto y la DI real lo resuelve.
NORMALIZE_URL = "https://servicios.usig.buenosaires.gob.ar/normalizar/"
CATASTRO_API_PARCELA_URL = (
    "https://datosabiertos-catastro-apis.buenosaires.gob.ar/catastro/parcela/"
)


def test_use_table_forwards_the_optional_address_to_the_port(
    client: TestClient, use_table_resolver: FakeResolver
) -> None:
    client.get(
        USE_TABLE_URL,
        params={"lat": -34.6040, "lng": -58.4055, "address": "CORRIENTES 2801"},
    )

    assert use_table_resolver.calls == [(-34.6040, -58.4055, "CORRIENTES 2801")]


@pytest.mark.parametrize("address", ["AB", "A" * 201])
def test_invalid_address_returns_422_without_resolving(
    client: TestClient, use_table_resolver: FakeResolver, address: str
) -> None:
    response = client.get(
        USE_TABLE_URL,
        params={"lat": -34.6040, "lng": -58.4055, "address": address},
    )

    assert response.status_code == 422
    assert use_table_resolver.calls == []


@respx.mock
def test_real_use_table_resolver_falls_back_to_the_official_address() -> None:
    """Sin dependency_overrides: el endpoint público usa la DI real y el fallback."""
    respx.get(f"{BASE}/catastro/parcela/").respond(200, json={})
    respx.get(NORMALIZE_URL).respond(
        200, json=load_fixture("normalizar_corrientes.json")
    )
    respx.get(CATASTRO_API_PARCELA_URL).respond(
        200, json=load_fixture("parcela_corrientes.json")
    )
    respx.get(f"{BASE}/cur3d/mixtura_usos/").respond(
        200, json=load_fixture("mixtura_usos.json")
    )
    respx.get(f"{BASE}/cur3d/categorias/").respond(
        200, json=load_fixture("categorias.json")
    )
    respx.get(f"{BASE}/cur3d/cuadrosdeuso/rubros/").respond(
        200, json=load_fixture("rubros.json")
    )

    response = TestClient(app).get(
        USE_TABLE_URL,
        params={"lat": -34.5000, "lng": -58.4000, "address": "CORRIENTES 2801"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["smp"] == "013-099-018"
    assert set(body) == {
        "smp",
        "official_address",
        "mix_area",
        "categories",
        "source",
        "limitations",
    }
    assert any("dirección" in item.lower() for item in body["limitations"])
