from collections.abc import Iterator
from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from conco.guidance.api import get_activity_directory, get_procedure_catalog
from conco.guidance.domain import (
    Activity,
    ActivityDirectoryError,
    ActivityProcedures,
    ActivitySuggestion,
    ApplicableProcedure,
    ContextAnswers,
    Procedure,
    Requirement,
    RequirementOrigin,
    Source,
)
from conco.main import app

SUGGEST_URL = "/guidance/activities"
PROCEDURES_URL = "/guidance/activities/peluqueria/procedures"

SOURCE = Source(
    name="Trámites del Gobierno de la Ciudad de Buenos Aires",
    url="https://buenosaires.gob.ar/gobierno/tramites",
    license="Creative Commons Reconocimiento 2.5 Argentina (CC BY 2.5 AR)",
)
SOURCE_JSON = {
    "name": "Trámites del Gobierno de la Ciudad de Buenos Aires",
    "url": "https://buenosaires.gob.ar/gobierno/tramites",
    "license": "Creative Commons Reconocimiento 2.5 Argentina (CC BY 2.5 AR)",
}
SUGGESTION = ActivitySuggestion(
    slug="peluqueria", name="Peluquería", matched_alias="barbería", similarity=0.8512
)
SUGGESTION_JSON = {
    "slug": "peluqueria",
    "name": "Peluquería",
    "matched_alias": "barbería",
    "similarity": 0.8512,
}
ACTIVITY_PROCEDURES = ActivityProcedures(
    activity=Activity(slug="peluqueria", name="Peluquería"),
    procedures=[
        ApplicableProcedure(
            procedure=Procedure(
                id=UUID("338718b4-a2a0-44af-baa4-083f5d834b12"),
                title="Habilitación de actividad económica",
                official_url="https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica",
                summary="Con este trámite podés solicitar la habilitación.",
                last_updated=datetime(2026, 8, 7, 18, 57, 1, tzinfo=UTC),
            ),
            note="Para abrir el local; requiere evaluación técnica.",
        ),
        ApplicableProcedure(
            procedure=Procedure(
                id=UUID("1fb7a579-8fc2-4216-b113-684cc272f7f1"),
                title="Inscripción en el Registro de Empleadores",
                official_url="https://buenosaires.gob.ar/tramites/registro-de-empleadores",
                summary="Registrate como empleador.",
                last_updated=datetime(2026, 8, 7, 18, 57, 1, tzinfo=UTC),
            ),
            note="Si vas a contratar personal.",
            applies_when=ContextAnswers(has_employees=True),
        ),
    ],
)
HABILITACION_JSON = {
    "procedure": {
        "id": "338718b4-a2a0-44af-baa4-083f5d834b12",
        "title": "Habilitación de actividad económica",
        "official_url": "https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica",
        "summary": "Con este trámite podés solicitar la habilitación.",
        "last_updated": "2026-08-07T18:57:01Z",
    },
    "note": "Para abrir el local; requiere evaluación técnica.",
    "status": "applies",
}
EMPLEADORES_JSON = {
    "procedure": {
        "id": "1fb7a579-8fc2-4216-b113-684cc272f7f1",
        "title": "Inscripción en el Registro de Empleadores",
        "official_url": "https://buenosaires.gob.ar/tramites/registro-de-empleadores",
        "summary": "Registrate como empleador.",
        "last_updated": "2026-08-07T18:57:01Z",
    },
    "note": "Si vas a contratar personal.",
    "status": "may_apply",
}
REQUIREMENTS_NOTE_TEXT = (
    "Fuente oficial: páginas de los trámites. Es una orientación general; "
    "verificá siempre con el organismo."
)
ACTIVITY_PROCEDURES_JSON = {
    "activity": {"slug": "peluqueria", "name": "Peluquería"},
    "questions": [
        {"id": "has_employees", "text": "¿Vas a contratar personal?", "answer": None}
    ],
    "procedures": [HABILITACION_JSON, EMPLEADORES_JSON],
    "excluded_count": 0,
    "excluded": [],
    "source": SOURCE_JSON,
    "requirements": [],
    "requirements_note": REQUIREMENTS_NOTE_TEXT,
}
REQUIREMENT = Requirement(
    id="req-0123456789ab",
    text="DNI del titular",
    heading="Documentación",
    origins=[
        RequirementOrigin(
            procedure_id=UUID("338718b4-a2a0-44af-baa4-083f5d834b12"),
            procedure_title="Habilitación de actividad económica",
            official_url="https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica",
        )
    ],
)
REQUIREMENT_JSON = {
    "id": "req-0123456789ab",
    "text": "DNI del titular",
    "heading": "Documentación",
    "origins": [
        {
            "procedure_id": "338718b4-a2a0-44af-baa4-083f5d834b12",
            "procedure_title": "Habilitación de actividad económica",
            "official_url": "https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica",
        }
    ],
}
ACTIVITIES_UNAVAILABLE_MESSAGE = (
    "La búsqueda de actividades no está disponible. Intentá de nuevo más tarde."
)


def error_json(response, code: str, detail: str) -> dict[str, str]:
    """Cuerpo esperado de un error propio, con el request id que devolvió la respuesta."""
    return {"code": code, "request_id": response.headers["x-request-id"], "detail": detail}


class FakeActivityDirectory:
    """Reemplaza a la base de actividades en los tests: devuelve datos fijos y anota cada llamada."""

    def __init__(self) -> None:
        self.suggestions: list[ActivitySuggestion] = [SUGGESTION]
        self.procedures: ActivityProcedures | None = ACTIVITY_PROCEDURES
        self.error: Exception | None = None
        self.suggest_calls: list[tuple[str, int]] = []
        self.procedures_calls: list[str] = []
        self.catalog_loaded = True
        self.catalog_error: Exception | None = None

    async def suggest(self, query: str, limit: int) -> list[ActivitySuggestion]:
        self.suggest_calls.append((query, limit))
        if self.error is not None:
            raise self.error
        return self.suggestions

    async def procedures_for(self, slug: str) -> ActivityProcedures | None:
        self.procedures_calls.append(slug)
        if self.error is not None:
            raise self.error
        return self.procedures

    async def catalog_ready(self) -> bool:
        if self.catalog_error is not None:
            raise self.catalog_error
        return self.catalog_loaded


class FakeProcedureCatalog:
    """Solo aporta la fuente oficial; anota cualquier llamada a la API de la Ciudad."""

    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []

    @property
    def source(self) -> Source:
        return SOURCE

    async def search(self, query: str, limit: int) -> list[Procedure]:
        self.calls.append(("search", query, limit))
        return []

    async def get(self, procedure_id: UUID) -> Procedure | None:
        self.calls.append(("get", procedure_id))
        return None


@pytest.fixture
def directory() -> FakeActivityDirectory:
    return FakeActivityDirectory()


@pytest.fixture
def catalog() -> FakeProcedureCatalog:
    return FakeProcedureCatalog()


@pytest.fixture
def client(
    directory: FakeActivityDirectory, catalog: FakeProcedureCatalog
) -> Iterator[TestClient]:
    app.dependency_overrides[get_activity_directory] = lambda: directory
    app.dependency_overrides[get_procedure_catalog] = lambda: catalog
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_suggest_returns_ranked_activities(client: TestClient) -> None:
    response = client.get(SUGGEST_URL, params={"query": "quiero poner una barbería"})

    assert response.status_code == 200
    assert response.json() == {"activities": [SUGGESTION_JSON]}


def test_suggest_uses_five_results_by_default(
    client: TestClient, directory: FakeActivityDirectory
) -> None:
    client.get(SUGGEST_URL, params={"query": "barbería"})

    assert directory.suggest_calls == [("barbería", 5)]


def test_suggest_forwards_limit(client: TestClient, directory: FakeActivityDirectory) -> None:
    client.get(SUGGEST_URL, params={"query": "barbería", "limit": 10})

    assert directory.suggest_calls == [("barbería", 10)]


def test_suggest_without_matches_returns_empty_list(
    client: TestClient, directory: FakeActivityDirectory
) -> None:
    directory.suggestions = []

    response = client.get(SUGGEST_URL, params={"query": "gimnasio"})

    assert response.status_code == 200
    assert response.json() == {"activities": []}


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"query": "a"},
        {"query": "   "},
        {"query": "x" * 101},
        {"query": "barbería", "limit": 0},
        {"query": "barbería", "limit": 11},
    ],
)
def test_suggest_rejects_invalid_parameters(
    client: TestClient, directory: FakeActivityDirectory, params: dict
) -> None:
    response = client.get(SUGGEST_URL, params=params)

    assert response.status_code == 422
    assert directory.suggest_calls == []


def test_suggest_returns_503_when_directory_fails(
    client: TestClient, directory: FakeActivityDirectory
) -> None:
    directory.error = ActivityDirectoryError("connection refused")

    response = client.get(SUGGEST_URL, params={"query": "barbería"})

    assert response.status_code == 503
    assert response.json() == error_json(
        response, "ACTIVITIES_UNAVAILABLE", ACTIVITIES_UNAVAILABLE_MESSAGE
    )


def test_procedures_returns_activity_procedures_and_source(
    client: TestClient, directory: FakeActivityDirectory
) -> None:
    response = client.get(PROCEDURES_URL)

    assert response.status_code == 200
    assert response.json() == ACTIVITY_PROCEDURES_JSON
    assert directory.procedures_calls == ["peluqueria"]


def test_procedures_returns_404_for_unknown_activity(
    client: TestClient, directory: FakeActivityDirectory
) -> None:
    directory.procedures = None

    response = client.get("/guidance/activities/gimnasio/procedures")

    assert response.status_code == 404
    assert response.json() == error_json(
        response, "ACTIVITY_NOT_FOUND", "No se encontró la actividad solicitada."
    )


def test_procedures_returns_503_while_the_catalog_is_still_loading(
    client: TestClient, directory: FakeActivityDirectory
) -> None:
    directory.procedures = None
    directory.catalog_loaded = False

    response = client.get(PROCEDURES_URL)

    assert response.status_code == 503
    assert response.json() == error_json(
        response, "PROCEDURES_LOADING", "Estamos cargando los trámites, volvé a intentar."
    )


@pytest.mark.parametrize("slug", ["Peluqueria", "pelu queria", "pelu_queria", "x" * 61])
def test_procedures_rejects_invalid_slug(
    client: TestClient, directory: FakeActivityDirectory, slug: str
) -> None:
    response = client.get(f"/guidance/activities/{slug}/procedures")

    assert response.status_code == 422
    assert directory.procedures_calls == []


def test_procedures_returns_503_when_directory_fails(
    client: TestClient, directory: FakeActivityDirectory
) -> None:
    directory.error = ActivityDirectoryError("connection refused")

    response = client.get(PROCEDURES_URL)

    assert response.status_code == 503
    assert response.json() == error_json(
        response,
        "PROCEDURES_UNAVAILABLE",
        "No pudimos consultar los trámites. Intentá de nuevo.",
    )


def test_procedures_answer_confirms_conditional_procedure(client: TestClient) -> None:
    response = client.get(PROCEDURES_URL, params={"has_employees": "true"})

    assert response.status_code == 200
    body = response.json()
    assert body["questions"] == [
        {"id": "has_employees", "text": "¿Vas a contratar personal?", "answer": True}
    ]
    assert body["procedures"] == [HABILITACION_JSON, {**EMPLEADORES_JSON, "status": "applies"}]
    assert body["excluded_count"] == 0


def test_procedures_answer_drops_contradicted_procedure(client: TestClient) -> None:
    response = client.get(PROCEDURES_URL, params={"has_employees": "false"})

    assert response.status_code == 200
    body = response.json()
    assert body["procedures"] == [HABILITACION_JSON]
    assert body["excluded_count"] == 1
    assert body["excluded"] == [
        {
            "id": "1fb7a579-8fc2-4216-b113-684cc272f7f1",
            "title": "Inscripción en el Registro de Empleadores",
            "because": ["has_employees"],
        }
    ]
    assert body["questions"][0]["answer"] is False


@pytest.mark.parametrize("params", [{"has_employees": "quizas"}, {"unknown_question": "true"}])
def test_procedures_rejects_invalid_answers(
    client: TestClient, directory: FakeActivityDirectory, params: dict
) -> None:
    response = client.get(PROCEDURES_URL, params=params)

    assert response.status_code == 422
    assert directory.procedures_calls == []


def test_procedures_response_includes_requirements_and_exact_note(
    client: TestClient, directory: FakeActivityDirectory
) -> None:
    directory.procedures = ACTIVITY_PROCEDURES.model_copy(update={"requirements": [REQUIREMENT]})

    response = client.get(PROCEDURES_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["requirements"] == [REQUIREMENT_JSON]
    assert body["requirements_note"] == (
        "Fuente oficial: páginas de los trámites. Es una orientación general; "
        "verificá siempre con el organismo."
    )


def test_procedures_keeps_requirements_when_all_procedures_are_filtered_out(
    client: TestClient, directory: FakeActivityDirectory
) -> None:
    conditional = ACTIVITY_PROCEDURES.procedures[1]
    directory.procedures = ActivityProcedures(
        activity=ACTIVITY_PROCEDURES.activity,
        procedures=[conditional],
        requirements=[REQUIREMENT],
    )

    response = client.get(PROCEDURES_URL, params={"has_employees": "false"})

    assert response.status_code == 200
    body = response.json()
    assert body["procedures"] == []
    assert body["excluded_count"] == 1
    assert body["requirements"] == [REQUIREMENT_JSON]


def test_procedures_preserves_existing_fields_and_does_not_call_the_city_api(
    client: TestClient,
    directory: FakeActivityDirectory,
    catalog: FakeProcedureCatalog,
) -> None:
    response = client.get(PROCEDURES_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["activity"] == ACTIVITY_PROCEDURES_JSON["activity"]
    assert body["questions"] == ACTIVITY_PROCEDURES_JSON["questions"]
    assert body["procedures"] == ACTIVITY_PROCEDURES_JSON["procedures"]
    assert body["excluded_count"] == ACTIVITY_PROCEDURES_JSON["excluded_count"]
    assert body["source"] == SOURCE_JSON
    assert catalog.calls == []

    filtered = client.get(PROCEDURES_URL, params={"has_employees": "false"}).json()
    assert filtered["procedures"] == [HABILITACION_JSON]
    assert filtered["excluded_count"] == 1
