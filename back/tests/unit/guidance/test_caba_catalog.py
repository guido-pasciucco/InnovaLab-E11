import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
import respx

from conco.config import settings
from conco.guidance.domain import Procedure, ProcedureSearchError, Source
from conco.guidance.infrastructure import CabaProcedureCatalog, html_to_text

pytestmark = pytest.mark.anyio

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures" / "caba_tramites"
PROCEDURES_URL = f"{settings.caba_tramites_base_url}/node/tramites_obelisco"
HABILITACION_ID = UUID("338718b4-a2a0-44af-baa4-083f5d834b12")
EVENTOS_ID = UUID("1640325c-304b-4684-97e4-781b9831a591")
UNKNOWN_ID = UUID("00000000-0000-0000-0000-000000000000")


def load_fixture(name: str) -> Any:
    """Lee una respuesta real de la API de trámites guardada en tests/fixtures/caba_tramites/."""
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def test_html_to_text_separates_blocks_and_keeps_inline_text_together() -> None:
    html = "<p>Contar con&nbsp;<strong>usuario</strong>.</p><p>Segundo<br>párrafo</p>"

    assert html_to_text(html) == "Contar con usuario. Segundo párrafo"


def test_html_to_text_decodes_entities_and_ignores_scripts() -> None:
    html = "<div>Planos &amp; permisos<script>alert('x')</script></div><ul><li>A</li><li>B</li></ul>"

    assert html_to_text(html) == "Planos & permisos A B"


def test_source_cites_the_official_catalog_and_its_license() -> None:
    assert CabaProcedureCatalog().source == Source(
        name="Trámites del Gobierno de la Ciudad de Buenos Aires",
        url="https://buenosaires.gob.ar/gobierno/tramites",
        license="Creative Commons Reconocimiento 2.5 Argentina (CC BY 2.5 AR)",
    )


@respx.mock
async def test_search_maps_results_to_domain_procedures() -> None:
    respx.get(PROCEDURES_URL).respond(200, json=load_fixture("busqueda_habilitaci.json"))

    procedures = await CabaProcedureCatalog().search("habilitaci", limit=10)

    assert len(procedures) == 10
    assert procedures[1] == Procedure(
        id=HABILITACION_ID,
        title="Habilitación de actividad económica",
        official_url="https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica",
        summary=(
            "Con este trámite podés solicitar la habilitación para realizar actividades "
            "comerciales en la Ciudad. Para obtenerla, tu local debe aprobar una "
            "evaluación técnica profesional."
        ),
        last_updated=datetime(2026, 8, 7, 18, 57, 1, tzinfo=UTC),
    )


@respx.mock
async def test_search_forwards_query_and_limit() -> None:
    route = respx.get(PROCEDURES_URL).respond(
        200, json=load_fixture("busqueda_sin_resultados.json")
    )

    await CabaProcedureCatalog().search("caf", limit=3)

    params = route.calls.last.request.url.params
    assert params["filter[title][value]"] == "caf"
    assert params["page[limit]"] == "3"


@respx.mock
async def test_search_without_results_returns_empty_list() -> None:
    respx.get(PROCEDURES_URL).respond(200, json=load_fixture("busqueda_sin_resultados.json"))

    assert await CabaProcedureCatalog().search("caf", limit=10) == []


@respx.mock
async def test_search_failure_raises_procedure_search_error() -> None:
    respx.get(PROCEDURES_URL).respond(400, json=load_fixture("error_400_filtro_invalido.json"))

    with pytest.raises(ProcedureSearchError):
        await CabaProcedureCatalog().search("habilitaci", limit=10)


@respx.mock
async def test_get_maps_requirements_steps_office_and_start_url() -> None:
    respx.get(f"{PROCEDURES_URL}/{HABILITACION_ID}").respond(
        200, json=load_fixture("tramite_habilitacion_actividad_economica.json")
    )

    detail = await CabaProcedureCatalog().get(HABILITACION_ID)

    assert detail is not None
    assert detail.title == "Habilitación de actividad económica"
    assert detail.official_url == (
        "https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica"
    )
    assert len(detail.requirements) == 11
    assert detail.requirements[0].startswith("Contar con usuario y clave miBA nivel 3.")
    assert detail.requirements[7] == (
        "En caso de corresponder la persona solicitante deberá presentar: "
        "Certificado de sobrecarga."
    )
    assert detail.requirements[10] == (
        "Importante: Recordá que, según la normativa vigente de la actividad económica "
        "que querés habilitar, se te podrá solicitar documentación específica."
    )
    assert len(detail.steps) == 5
    assert detail.steps[1] == (
        "Agregá los datos de la persona titular o firmante: Ingresá el CUIT de la "
        "persona solicitante o firmante. Estas personas pueden ser tanto físicas como "
        "jurídicas."
    )
    assert detail.responsible_office == (
        "Agencia Gubernamental de Control - Dirección General de Habilitaciones y Permisos"
    )
    assert detail.start_url is not None
    assert detail.start_url.startswith("https://login.buenosaires.gob.ar/")


@respx.mock
async def test_get_without_start_button_has_no_start_url() -> None:
    respx.get(f"{PROCEDURES_URL}/{EVENTOS_ID}").respond(
        200, json=load_fixture("tramite_sin_boton_iniciar.json")
    )

    detail = await CabaProcedureCatalog().get(EVENTOS_ID)

    assert detail is not None
    assert detail.start_url is None
    assert detail.steps[0].startswith("Generar expediente: ")


@respx.mock
async def test_step_without_explanation_keeps_only_its_title() -> None:
    payload = load_fixture("tramite_sin_boton_iniciar.json")
    for resource in payload["included"]:
        if resource["type"] == "paragraph--item_titulo_del_paso":
            resource["attributes"]["field_parrafo"] = None
    respx.get(f"{PROCEDURES_URL}/{EVENTOS_ID}").respond(200, json=payload)

    detail = await CabaProcedureCatalog().get(EVENTOS_ID)

    assert detail is not None
    assert detail.steps == [
        "Generar expediente",
        "Cargar la documentación",
        "Finalizar el trámite",
    ]


@respx.mock
async def test_get_unknown_procedure_returns_none() -> None:
    respx.get(f"{PROCEDURES_URL}/{UNKNOWN_ID}").respond(
        301,
        text=(FIXTURES_DIR / "tramite_inexistente_301.html").read_text(encoding="utf-8"),
        headers={"Location": "https://buenosaires.gob.ar/gcaba_historico/jsonapi"},
    )

    assert await CabaProcedureCatalog().get(UNKNOWN_ID) is None


@respx.mock
async def test_get_failure_raises_procedure_search_error() -> None:
    respx.get(f"{PROCEDURES_URL}/{HABILITACION_ID}").respond(500, text="Internal Server Error")

    with pytest.raises(ProcedureSearchError):
        await CabaProcedureCatalog().get(HABILITACION_ID)
