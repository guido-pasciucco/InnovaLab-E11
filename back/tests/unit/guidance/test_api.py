from collections.abc import Iterator
from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from conco.guidance.api import get_procedure_catalog
from conco.guidance.domain import (
    Procedure,
    ProcedureDetail,
    ProcedureSearchError,
    Source,
)
from conco.main import app

SEARCH_URL = "/guidance/procedures"
PROCEDURE_ID = UUID("338718b4-a2a0-44af-baa4-083f5d834b12")
DETAIL_URL = f"{SEARCH_URL}/{PROCEDURE_ID}"

SOURCE = Source(
    name="Trámites del Gobierno de la Ciudad de Buenos Aires",
    url="https://buenosaires.gob.ar/gobierno/tramites",
    license="Creative Commons Reconocimiento 2.5 Argentina (CC BY 2.5 AR)",
)
SAMPLE_PROCEDURE = Procedure(
    id=PROCEDURE_ID,
    title="Habilitación de actividad económica",
    official_url="https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica",
    summary="Con este trámite podés solicitar la habilitación.",
    last_updated=datetime(2026, 8, 7, 18, 57, 1, tzinfo=UTC),
)
SAMPLE_DETAIL = ProcedureDetail(
    **SAMPLE_PROCEDURE.model_dump(),
    requirements=["Contar con usuario y clave miBA nivel 3."],
    steps=["Iniciá tu solicitud: Hacé clic en “Iniciar trámite”."],
    responsible_office="Agencia Gubernamental de Control",
    start_url="https://login.buenosaires.gob.ar/",
)

PROCEDURE_JSON = {
    "id": "338718b4-a2a0-44af-baa4-083f5d834b12",
    "title": "Habilitación de actividad económica",
    "official_url": "https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica",
    "summary": "Con este trámite podés solicitar la habilitación.",
    "last_updated": "2026-08-07T18:57:01Z",
}
SOURCE_JSON = {
    "name": "Trámites del Gobierno de la Ciudad de Buenos Aires",
    "url": "https://buenosaires.gob.ar/gobierno/tramites",
    "license": "Creative Commons Reconocimiento 2.5 Argentina (CC BY 2.5 AR)",
}


class FakeProcedureCatalog:
    """Reemplaza a la API de la Ciudad en los tests: devuelve datos fijos y anota cada llamada."""

    def __init__(self) -> None:
        self.procedures: list[Procedure] = [SAMPLE_PROCEDURE]
        self.detail: ProcedureDetail | None = SAMPLE_DETAIL
        self.error: Exception | None = None
        self.search_calls: list[tuple[str, int]] = []
        self.get_calls: list[UUID] = []

    @property
    def source(self) -> Source:
        return SOURCE

    async def search(self, query: str, limit: int) -> list[Procedure]:
        self.search_calls.append((query, limit))
        if self.error is not None:
            raise self.error
        return self.procedures

    async def get(self, procedure_id: UUID) -> ProcedureDetail | None:
        self.get_calls.append(procedure_id)
        if self.error is not None:
            raise self.error
        return self.detail


@pytest.fixture
def catalog() -> FakeProcedureCatalog:
    return FakeProcedureCatalog()


@pytest.fixture
def client(catalog: FakeProcedureCatalog) -> Iterator[TestClient]:
    app.dependency_overrides[get_procedure_catalog] = lambda: catalog
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_search_returns_procedures_and_their_source(client: TestClient) -> None:
    response = client.get(SEARCH_URL, params={"query": "habilitación"})

    assert response.status_code == 200
    assert response.json() == {"procedures": [PROCEDURE_JSON], "source": SOURCE_JSON}


def test_search_uses_ten_results_by_default(
    client: TestClient, catalog: FakeProcedureCatalog
) -> None:
    client.get(SEARCH_URL, params={"query": "habilitación"})

    assert catalog.search_calls == [("habilitación", 10)]


def test_search_forwards_limit(client: TestClient, catalog: FakeProcedureCatalog) -> None:
    client.get(SEARCH_URL, params={"query": "gastronómico", "limit": 20})

    assert catalog.search_calls == [("gastronómico", 20)]


def test_search_without_results_returns_empty_list_with_source(
    client: TestClient, catalog: FakeProcedureCatalog
) -> None:
    catalog.procedures = []

    response = client.get(SEARCH_URL, params={"query": "caf"})

    assert response.status_code == 200
    assert response.json() == {"procedures": [], "source": SOURCE_JSON}


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"query": "ab"},
        {"query": "   "},
        {"query": "a" * 101},
        {"query": "habilitación", "limit": 0},
        {"query": "habilitación", "limit": 21},
    ],
)
def test_search_invalid_query_returns_422_without_calling_the_catalog(
    client: TestClient, catalog: FakeProcedureCatalog, params: dict[str, object]
) -> None:
    response = client.get(SEARCH_URL, params=params)

    assert response.status_code == 422
    assert catalog.search_calls == []


def test_search_error_returns_502(client: TestClient, catalog: FakeProcedureCatalog) -> None:
    catalog.error = ProcedureSearchError("La API no responde")

    response = client.get(SEARCH_URL, params={"query": "habilitación"})

    assert response.status_code == 502
    assert response.json() == {
        "detail": "El servicio de trámites no está disponible. Intentá de nuevo más tarde."
    }


def test_detail_returns_the_procedure_and_its_source(
    client: TestClient, catalog: FakeProcedureCatalog
) -> None:
    response = client.get(DETAIL_URL)

    assert response.status_code == 200
    assert response.json() == {
        "procedure": {
            **PROCEDURE_JSON,
            "requirements": ["Contar con usuario y clave miBA nivel 3."],
            "steps": ["Iniciá tu solicitud: Hacé clic en “Iniciar trámite”."],
            "responsible_office": "Agencia Gubernamental de Control",
            "start_url": "https://login.buenosaires.gob.ar/",
        },
        "source": SOURCE_JSON,
    }
    assert catalog.get_calls == [PROCEDURE_ID]


def test_detail_unknown_procedure_returns_404(
    client: TestClient, catalog: FakeProcedureCatalog
) -> None:
    catalog.detail = None

    response = client.get(DETAIL_URL)

    assert response.status_code == 404
    assert response.json() == {"detail": "No se encontró el trámite solicitado."}


def test_detail_error_returns_502(client: TestClient, catalog: FakeProcedureCatalog) -> None:
    catalog.error = ProcedureSearchError("La API no responde")

    response = client.get(DETAIL_URL)

    assert response.status_code == 502


def test_detail_invalid_id_returns_422_without_calling_the_catalog(
    client: TestClient, catalog: FakeProcedureCatalog
) -> None:
    response = client.get(f"{SEARCH_URL}/no-es-un-uuid")

    assert response.status_code == 422
    assert catalog.get_calls == []
