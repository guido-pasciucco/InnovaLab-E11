import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
import pytest
import respx

from conco.config import settings
from conco.integrations.caba_tramites.client import (
    CabaTramitesError,
    get_procedure,
    normalize_query,
    search_procedures,
)

pytestmark = pytest.mark.anyio

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures" / "caba_tramites"
PROCEDURES_URL = f"{settings.caba_tramites_base_url}/node/tramites_obelisco"
HABILITACION_ID = UUID("338718b4-a2a0-44af-baa4-083f5d834b12")
HABILITACION_URL = f"{PROCEDURES_URL}/{HABILITACION_ID}"
EVENTOS_ID = UUID("1640325c-304b-4684-97e4-781b9831a591")
EVENTOS_URL = f"{PROCEDURES_URL}/{EVENTOS_ID}"
UNKNOWN_ID = UUID("00000000-0000-0000-0000-000000000000")
UNKNOWN_URL = f"{PROCEDURES_URL}/{UNKNOWN_ID}"


def load_fixture(name: str) -> Any:
    """Lee una respuesta real de la API de trámites guardada en tests/fixtures/caba_tramites/."""
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def read_fixture_text(name: str) -> str:
    """Lee una respuesta real que no es JSON (por ejemplo, la página HTML de redirección)."""
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def test_normalize_query_removes_extra_spaces() -> None:
    assert normalize_query("  habilitación   comercial ") == "habilitación comercial"


@respx.mock
async def test_search_procedures_parses_the_results() -> None:
    respx.get(PROCEDURES_URL).respond(200, json=load_fixture("busqueda_habilitaci.json"))

    result = await search_procedures("habilitaci")

    assert len(result.procedures) == 10
    procedure = result.procedures[1]
    assert procedure.id == HABILITACION_ID
    assert procedure.attributes.title == "Habilitación de actividad económica"
    assert procedure.attributes.path.alias == "/tramites/habilitacion-de-actividad-economica"
    assert procedure.attributes.changed == datetime(2026, 8, 7, 18, 57, 1, tzinfo=UTC)
    assert procedure.attributes.body.format == "plain_text"
    assert procedure.attributes.body.value.startswith("Con este trámite podés solicitar")


@respx.mock
async def test_search_procedures_sends_jsonapi_filters() -> None:
    route = respx.get(PROCEDURES_URL).respond(
        200, json=load_fixture("busqueda_habilitaci.json")
    )

    await search_procedures("  habilitaci  ", limit=7)

    params = route.calls.last.request.url.params
    assert params["filter[status]"] == "1"
    assert params["filter[title][operator]"] == "CONTAINS"
    assert params["filter[title][value]"] == "habilitaci"
    assert params["sort"] == "title"
    assert params["page[limit]"] == "7"
    assert params["fields[node--tramites_obelisco]"] == "title,path,changed,body"


@respx.mock
async def test_search_procedures_without_results_returns_empty_list() -> None:
    respx.get(PROCEDURES_URL).respond(
        200, json=load_fixture("busqueda_sin_resultados.json")
    )

    result = await search_procedures("caf")

    assert result.procedures == []


@respx.mock
async def test_search_procedures_http_error_raises_caba_tramites_error() -> None:
    respx.get(PROCEDURES_URL).respond(
        400, json=load_fixture("error_400_filtro_invalido.json")
    )

    with pytest.raises(CabaTramitesError):
        await search_procedures("habilitaci")


@respx.mock
async def test_search_procedures_timeout_raises_caba_tramites_error() -> None:
    respx.get(PROCEDURES_URL).mock(side_effect=httpx.ConnectTimeout("timeout"))

    with pytest.raises(CabaTramitesError):
        await search_procedures("habilitaci")


@respx.mock
async def test_search_procedures_unexpected_payload_raises_caba_tramites_error() -> None:
    respx.get(PROCEDURES_URL).respond(200, json={"foo": 1})

    with pytest.raises(CabaTramitesError):
        await search_procedures("habilitaci")


@respx.mock
async def test_search_procedures_non_json_body_raises_caba_tramites_error() -> None:
    respx.get(PROCEDURES_URL).respond(200, text="<html>Mantenimiento</html>")

    with pytest.raises(CabaTramitesError):
        await search_procedures("habilitaci")


@respx.mock
async def test_get_procedure_parses_requirements_steps_office_and_start_link() -> None:
    respx.get(HABILITACION_URL).respond(
        200, json=load_fixture("tramite_habilitacion_actividad_economica.json")
    )

    detail = await get_procedure(HABILITACION_ID)

    assert detail is not None
    assert detail.procedure.id == HABILITACION_ID
    assert detail.procedure.attributes.title == "Habilitación de actividad económica"
    assert [item.heading for item in detail.requirements] == [
        None,
        "El profesional tendrá consideraciones especiales",
        "En caso de corresponder la persona solicitante deberá presentar",
        "Importante",
    ]
    assert [len(item.bodies) for item in detail.requirements] == [3, 4, 3, 1]
    assert detail.requirements[2].bodies[0].value == "<p>Certificado de sobrecarga.</p>"
    assert [step.title for step in detail.steps] == [
        "Iniciá tu solicitud",
        "Agregá los datos de la persona titular o firmante",
        "Declará la ubicación de tu establecimiento",
        "Solicitá el certificado de Aptitud Ambiental",
        "Al finalizar el trámite",
    ]
    assert detail.steps[1].text is not None
    assert detail.steps[1].text.format == "full_html"
    assert detail.responsible_office is not None
    assert detail.responsible_office.name == (
        "Agencia Gubernamental de Control - Dirección General de Habilitaciones y Permisos "
    )
    assert detail.start_button is not None
    assert detail.start_button.link.uri.startswith("https://login.buenosaires.gob.ar/")


@respx.mock
async def test_get_procedure_without_start_button_returns_none_button() -> None:
    respx.get(EVENTOS_URL).respond(200, json=load_fixture("tramite_sin_boton_iniciar.json"))

    detail = await get_procedure(EVENTOS_ID)

    assert detail is not None
    assert detail.start_button is None
    assert [item.heading for item in detail.requirements] == [
        "Requisitos obligatorios",
        "Requisitos opcionales",
        "Documentación adicional para estructuras fijas y móviles",
        "Documentación adicional para instalaciones fijas y móviles",
    ]
    assert len(detail.steps) == 3


@respx.mock
async def test_get_procedure_requests_only_the_needed_paragraphs() -> None:
    route = respx.get(HABILITACION_URL).respond(
        200, json=load_fixture("tramite_habilitacion_actividad_economica.json")
    )

    await get_procedure(HABILITACION_ID)

    params = route.calls.last.request.url.params
    include = params["include"].split(",")
    assert (
        "field_contenido.field_seccion.field_columna_izquierda.field_componente"
        ".field_item_requisito_tramite"
    ) in include
    assert (
        "field_contenido.field_seccion.field_columna_izquierda.field_componente"
        ".field_item_paso_del_tramite"
    ) in include
    assert params["fields[node--tramites_obelisco]"] == "title,path,changed,body,field_contenido"
    assert params["fields[paragraph--item_requisito_tramite]"] == "field_texto,field_cuerpo"
    assert params["fields[paragraph--parrafo]"] == ""


@respx.mock
async def test_get_procedure_redirect_means_not_found() -> None:
    respx.get(UNKNOWN_URL).respond(
        301,
        text=read_fixture_text("tramite_inexistente_301.html"),
        headers={
            "Location": (
                "https://buenosaires.gob.ar/gcaba_historico/jsonapi/node/"
                f"tramites_obelisco/{UNKNOWN_ID}"
            )
        },
    )

    assert await get_procedure(UNKNOWN_ID) is None


@respx.mock
async def test_get_procedure_server_error_raises_caba_tramites_error() -> None:
    respx.get(HABILITACION_URL).respond(500, text="Internal Server Error")

    with pytest.raises(CabaTramitesError):
        await get_procedure(HABILITACION_ID)


@respx.mock
async def test_get_procedure_timeout_raises_caba_tramites_error() -> None:
    respx.get(HABILITACION_URL).mock(side_effect=httpx.ReadTimeout("timeout"))

    with pytest.raises(CabaTramitesError):
        await get_procedure(HABILITACION_ID)


@respx.mock
async def test_get_procedure_non_json_body_raises_caba_tramites_error() -> None:
    respx.get(HABILITACION_URL).respond(200, text="<html>Mantenimiento</html>")

    with pytest.raises(CabaTramitesError):
        await get_procedure(HABILITACION_ID)


@respx.mock
async def test_get_procedure_unexpected_paragraph_shape_raises_caba_tramites_error() -> None:
    payload = load_fixture("tramite_habilitacion_actividad_economica.json")
    for resource in payload["included"]:
        if resource["type"] == "paragraph--item_titulo_del_paso":
            resource["attributes"]["field_titulo"] = None
    respx.get(HABILITACION_URL).respond(200, json=payload)

    with pytest.raises(CabaTramitesError):
        await get_procedure(HABILITACION_ID)
