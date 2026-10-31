from collections.abc import Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient

from conco.guidance.api import get_regulation_registry
from conco.guidance.domain import Regulation, RegulationLookupError, RegulationType, Source
from conco.main import app

REGULATIONS_URL = "/guidance/regulations"

SOURCE = Source(
    name="Boletín Oficial de la Ciudad de Buenos Aires",
    url="https://boletinoficial.buenosaires.gob.ar",
    license=(
        "Sin licencia explícita: normas oficiales de publicación obligatoria y acceso "
        "público"
    ),
)
LEY_6101 = Regulation(
    type=RegulationType.LEY,
    number=6101,
    year=2018,
    summary="Ley Marco de Regulación de actividades económicas",
    issuing_body="Legislatura de la Ciudad de Buenos Aires",
    publication_date=date(2018, 12, 27),
    bulletin_number=5526,
    document_url="https://api-restboletinoficial.buenosaires.gob.ar/download/1255476",
)


class FakeRegulationRegistry:
    """Reemplaza al Boletín Oficial en los tests: devuelve datos fijos y anota cada llamada."""

    def __init__(self) -> None:
        self.regulations: list[Regulation] = [LEY_6101]
        self.error: Exception | None = None
        self.calls: list[tuple[RegulationType, int, int]] = []

    @property
    def source(self) -> Source:
        return SOURCE

    async def find(
        self, regulation_type: RegulationType, number: int, year: int
    ) -> list[Regulation]:
        self.calls.append((regulation_type, number, year))
        if self.error is not None:
            raise self.error
        return self.regulations


@pytest.fixture
def registry() -> FakeRegulationRegistry:
    return FakeRegulationRegistry()


@pytest.fixture
def client(registry: FakeRegulationRegistry) -> Iterator[TestClient]:
    app.dependency_overrides[get_regulation_registry] = lambda: registry
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_returns_the_regulation_and_its_source(
    client: TestClient, registry: FakeRegulationRegistry
) -> None:
    response = client.get(f"{REGULATIONS_URL}/ley/6101/2018")

    assert response.status_code == 200
    assert response.json() == {
        "regulations": [
            {
                "type": "ley",
                "number": 6101,
                "year": 2018,
                "summary": "Ley Marco de Regulación de actividades económicas",
                "issuing_body": "Legislatura de la Ciudad de Buenos Aires",
                "publication_date": "2018-12-27",
                "bulletin_number": 5526,
                "document_url": (
                    "https://api-restboletinoficial.buenosaires.gob.ar/download/1255476"
                ),
            }
        ],
        "source": {
            "name": "Boletín Oficial de la Ciudad de Buenos Aires",
            "url": "https://boletinoficial.buenosaires.gob.ar",
            "license": (
                "Sin licencia explícita: normas oficiales de publicación obligatoria y acceso "
                "público"
            ),
        },
    }
    assert registry.calls == [(RegulationType.LEY, 6101, 2018)]


def test_forwards_decree_type(client: TestClient, registry: FakeRegulationRegistry) -> None:
    client.get(f"{REGULATIONS_URL}/decreto/40/2019")

    assert registry.calls == [(RegulationType.DECRETO, 40, 2019)]


def test_unknown_regulation_returns_404(
    client: TestClient, registry: FakeRegulationRegistry
) -> None:
    registry.regulations = []

    response = client.get(f"{REGULATIONS_URL}/ley/6101/2019")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "No se encontró la norma solicitada en el Boletín Oficial."
    }


def test_source_failure_returns_502(client: TestClient, registry: FakeRegulationRegistry) -> None:
    registry.error = RegulationLookupError("El Boletín no responde")

    response = client.get(f"{REGULATIONS_URL}/ley/6101/2018")

    assert response.status_code == 502
    assert response.json() == {
        "detail": "El Boletín Oficial no está disponible. Intentá de nuevo más tarde."
    }


@pytest.mark.parametrize(
    "path",
    [
        "resolucion/100/2019",
        "LEY/6101/2018",
        "ley/0/2018",
        "ley/-1/2018",
        "ley/abc/2018",
        "ley/6101/18",
        "ley/6101/1899",
        "ley/6101/2101",
    ],
)
def test_invalid_params_return_422_without_calling_the_registry(
    client: TestClient, registry: FakeRegulationRegistry, path: str
) -> None:
    response = client.get(f"{REGULATIONS_URL}/{path}")

    assert response.status_code == 422
    assert registry.calls == []
