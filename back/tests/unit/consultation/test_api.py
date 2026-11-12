"""Tests del endpoint de consultas (sin IA: orientación curada y etiquetada)."""

import base64
import json
from collections.abc import Iterator
from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from conco.consultation.api import (
    get_address_geocoder,
    get_activity_directory_for_consultation,
    get_procedure_catalog_for_consultation,
)
from conco.guidance.domain import (
    Activity,
    ActivityDirectoryError,
    ActivityProcedures,
    ActivitySuggestion,
    ApplicableProcedure,
    ContextAnswers,
    Procedure,
    Source,
)
from conco.main import app

URL = "/consultations"

SOURCE = Source(
    name="Trámites del Gobierno de la Ciudad de Buenos Aires",
    url="https://buenosaires.gob.ar/gobierno/tramites",
    license="Creative Commons Reconocimiento 2.5 Argentina (CC BY 2.5 AR)",
)
SUGGESTION = ActivitySuggestion(
    slug="peluqueria", name="Peluquería", matched_alias="barbería", similarity=0.8512
)
HABILITACION = Procedure(
    id=UUID("338718b4-a2a0-44af-baa4-083f5d834b12"),
    title="Habilitación de actividad económica",
    official_url="https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica",
    summary="Con este trámite podés solicitar la habilitación.",
    last_updated=datetime(2026, 8, 7, 18, 57, 1, tzinfo=UTC),
)
EMPLEADORES = Procedure(
    id=UUID("1fb7a579-8fc2-4216-b113-684cc272f7f1"),
    title="Inscripción en el Registro de Empleadores",
    official_url="https://buenosaires.gob.ar/tramites/registro-de-empleadores",
    summary="Registrate como empleador.",
    last_updated=datetime(2026, 8, 7, 18, 57, 1, tzinfo=UTC),
)
ACTIVITY_PROCEDURES = ActivityProcedures(
    activity=Activity(slug="peluqueria", name="Peluquería"),
    procedures=[
        ApplicableProcedure(procedure=HABILITACION, note="Para abrir el local."),
        ApplicableProcedure(
            procedure=EMPLEADORES,
            note="Si vas a contratar personal.",
            applies_when=ContextAnswers(has_employees=True),
        ),
    ],
)
PAYLOAD = {
    "activity": "quiero poner una barbería",
    "address": "Corrientes 2500",
    "point": {"lat": -34.6042, "lng": -58.3816},
    "activitySlug": "peluqueria",
}


class FakeActivityDirectory:
    """Reemplaza a la base de actividades en los tests: datos fijos y anotación de llamadas."""

    def __init__(self) -> None:
        self.suggestions: list[ActivitySuggestion] = [SUGGESTION]
        self.procedures: ActivityProcedures | None = ACTIVITY_PROCEDURES
        self.error: Exception | None = None
        self.suggest_calls: list[tuple[str, int]] = []
        self.procedures_calls: list[str] = []

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


class FakeProcedureCatalog:
    @property
    def source(self) -> Source:
        return SOURCE


class FakeGeocoder:
    """Reemplaza a Georef: devuelve una dirección normalizada fija o lanza el error indicado."""

    def __init__(self, result: tuple[str, dict | None] | Exception | None = None) -> None:
        self.result = result
        self.calls: list[str] = []

    async def geocode(self, address: str) -> tuple[str, dict | None] | None:
        self.calls.append(address)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def decode_slug(consultation_id: str) -> dict[str, str]:
    payload = consultation_id.removeprefix("c_")
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


@pytest.fixture
def directory() -> FakeActivityDirectory:
    return FakeActivityDirectory()


@pytest.fixture
def geocoder() -> FakeGeocoder:
    return FakeGeocoder()


@pytest.fixture
def client(directory: FakeActivityDirectory, geocoder: FakeGeocoder) -> Iterator[TestClient]:
    app.dependency_overrides[get_activity_directory_for_consultation] = lambda: directory
    app.dependency_overrides[get_procedure_catalog_for_consultation] = FakeProcedureCatalog
    app.dependency_overrides[get_address_geocoder] = lambda: geocoder
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_consultation_returns_the_camel_case_contract(client: TestClient) -> None:
    response = client.post(URL, json=PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "consultationId",
        "interpretedActivity",
        "normalizedAddress",
        "point",
        "summary",
        "steps",
        "territorialFeatures",
        "sources",
        "limitations",
    }
    assert body["interpretedActivity"] == "Peluquería"
    assert body["normalizedAddress"] == PAYLOAD["address"]
    assert body["point"] == PAYLOAD["point"]
    assert decode_slug(body["consultationId"]) == {"s": "peluqueria"}
    assert [step["id"] for step in body["steps"]] == ["step-1", "step-2", "step-3", "step-4"]
    assert body["territorialFeatures"] == []
    assert body["sources"][0]["id"] == "caba-tramites"
    assert body["sources"][0]["publisher"] == "Gobierno de la Ciudad de Buenos Aires"
    assert "retrievedAt" in body["sources"][0]
    assert body["limitations"]


def test_consultation_uses_the_provided_slug_without_calling_suggest(
    client: TestClient, directory: FakeActivityDirectory
) -> None:
    client.post(URL, json=PAYLOAD)

    assert directory.procedures_calls == ["peluqueria"]
    assert directory.suggest_calls == []


def test_consultation_without_slug_uses_the_top_suggestion(
    client: TestClient, directory: FakeActivityDirectory
) -> None:
    payload = {key: value for key, value in PAYLOAD.items() if key != "activitySlug"}

    body = client.post(URL, json=payload).json()

    assert directory.suggest_calls == [(payload["activity"], 1)]
    assert directory.procedures_calls == ["peluqueria"]
    assert body["interpretedActivity"] == "Peluquería"


def test_consultation_without_catalog_match_returns_generic_guidance(
    client: TestClient, directory: FakeActivityDirectory
) -> None:
    directory.suggestions = []
    payload = {key: value for key, value in PAYLOAD.items() if key != "activitySlug"}

    response = client.post(URL, json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["interpretedActivity"] == payload["activity"]
    assert any("catálogo" in limitation for limitation in body["limitations"])
    assert [step["id"] for step in body["steps"]] == ["step-1", "step-2", "step-3"]


def test_consultation_without_point_geocodes_the_address(
    client: TestClient, geocoder: FakeGeocoder
) -> None:
    geocoder.result = (
        "AV CORRIENTES 2500, Ciudad Autónoma de Buenos Aires",
        {"lat": -34.6047, "lng": -58.4021},
    )
    payload = {key: value for key, value in PAYLOAD.items() if key != "point"}

    body = client.post(URL, json=payload).json()

    assert geocoder.calls == ["Corrientes 2500"]
    assert body["normalizedAddress"] == "AV CORRIENTES 2500, Ciudad Autónoma de Buenos Aires"
    assert body["point"] == {"lat": -34.6047, "lng": -58.4021}
    assert [source["id"] for source in body["sources"]] == ["caba-tramites", "georef"]


def test_consultation_geocoder_failure_adds_a_limitation(
    client: TestClient, geocoder: FakeGeocoder
) -> None:
    geocoder.result = RuntimeError("georef caído")
    payload = {key: value for key, value in PAYLOAD.items() if key != "point"}

    response = client.post(URL, json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["point"] is None
    assert any("dirección" in limitation.lower() for limitation in body["limitations"])
    assert [source["id"] for source in body["sources"]] == ["caba-tramites"]


def test_consultation_when_directory_is_down_returns_503(
    client: TestClient, directory: FakeActivityDirectory
) -> None:
    directory.error = ActivityDirectoryError("boom")

    response = client.post(URL, json=PAYLOAD)

    assert response.status_code == 503
    assert response.json() == {
        "detail": "El servicio de consultas no está disponible. Intentá de nuevo más tarde."
    }


def test_follow_up_answers_with_the_curated_sources(client: TestClient) -> None:
    consultation = client.post(URL, json=PAYLOAD).json()

    response = client.post(
        f"/consultations/{consultation['consultationId']}/follow-up",
        json={"question": "¿Necesito contador?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "Habilitación de actividad económica" in body["answer"]
    assert body["sourceIds"] == ["caba-tramites"]
    assert body["limitations"]


def test_follow_up_rejects_an_invalid_id(client: TestClient) -> None:
    response = client.post(
        "/consultations/c_no-es-base64!!/follow-up",
        json={"question": "¿Y ahora?"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Identificador de consulta inválido."}


def test_follow_up_without_activity_gives_a_generic_answer(client: TestClient) -> None:
    consultation_id = "c_" + base64.urlsafe_b64encode(json.dumps({"s": ""}).encode()).decode().rstrip("=")

    response = client.post(
        f"/consultations/{consultation_id}/follow-up",
        json={"question": "¿Y ahora?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["sourceIds"] == ["caba-tramites"]
    assert body["limitations"]
