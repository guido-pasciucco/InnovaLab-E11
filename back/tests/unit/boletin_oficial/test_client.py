from datetime import date
from pathlib import Path

import httpx
import pytest
import respx

from conco.config import settings
from conco.integrations.boletin_oficial.client import (
    BoletinOficialError,
    BoletinOficialNormType,
    find_norms,
)

pytestmark = pytest.mark.anyio

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures" / "boletin_oficial"
RESULTS_URL = f"{settings.boletin_oficial_base_url}/obtenerResultado"
LEY_6101_2018_URL = f"{RESULTS_URL}/tipoNorma=1&nNorma=6101&anio=2018"
DECRETO_40_URL = f"{RESULTS_URL}/tipoNorma=2&nNorma=40"

# Content-Type que el Boletín declaró en cada respuesta real guardada en las fixtures.
JSON = "application/json"
HTML = "text/html; charset=UTF-8"


def read_fixture(name: str) -> bytes:
    """Lee una respuesta real del Boletín Oficial guardada en tests/fixtures/boletin_oficial/."""
    return (FIXTURES_DIR / name).read_bytes()


def respond_with_fixture(url: str, name: str, content_type: str = JSON) -> respx.Route:
    """Simula el Boletín devolviendo una respuesta real con el Content-Type que declaró."""
    return respx.get(url).respond(
        200, content=read_fixture(name), headers={"Content-Type": content_type}
    )


@respx.mock
async def test_finds_a_law_by_type_number_and_year() -> None:
    respond_with_fixture(LEY_6101_2018_URL, "ley_6101_2018.json")

    norms = await find_norms(BoletinOficialNormType.LEY, 6101, 2018)

    assert len(norms) == 1
    norm = norms[0]
    assert norm.id == 435567
    assert norm.type_name == "Ley"
    assert norm.number == 6101
    assert norm.summary.startswith("Ley Marco de Regulación de actividades económicas")
    assert norm.issuing_body == "Legislatura de la Ciudad de Buenos Aires"
    assert norm.bulletins[0].bulletin_number == 5526
    assert norm.bulletins[0].publication_date == date(2018, 12, 27)
    assert norm.documents[0].publication_date == date(2018, 12, 27)


@respx.mock
async def test_sends_every_filter_inside_the_path() -> None:
    route = respond_with_fixture(LEY_6101_2018_URL, "ley_6101_2018.json")

    await find_norms(BoletinOficialNormType.LEY, 6101, 2018)

    request = route.calls.last.request
    assert request.url.raw_path == b"/obtenerResultado/tipoNorma=1&nNorma=6101&anio=2018"
    assert request.url.query == b""


@respx.mock
async def test_finds_a_decree_by_type_number_and_year() -> None:
    respond_with_fixture(f"{DECRETO_40_URL}&anio=2019", "decreto_40_2019.json")

    norms = await find_norms(BoletinOficialNormType.DECRETO, 40, 2019)

    assert [norm.id for norm in norms] == [438789]
    assert norms[0].type_name == "Decreto"
    assert norms[0].summary == "Se aprueba la reglamentación de la Ley N° 6101"
    assert norms[0].issuing_body == "Área Jefe de Gobierno"


@respx.mock
async def test_rewrites_download_links_to_https() -> None:
    respond_with_fixture(LEY_6101_2018_URL, "ley_6101_2018.json")

    norm = (await find_norms(BoletinOficialNormType.LEY, 6101, 2018))[0]

    assert norm.documents[0].url == (
        "https://api-restboletinoficial.buenosaires.gob.ar/download/1255476"
    )
    assert norm.bulletins[0].url == (
        "https://api-restboletinoficial.buenosaires.gob.ar/download/1255814"
    )


@respx.mock
async def test_old_norm_without_document_link_or_issuing_body() -> None:
    respond_with_fixture(f"{DECRETO_40_URL}&anio=2010", "decreto_40_2010.json")

    norms = await find_norms(BoletinOficialNormType.DECRETO, 40, 2010)

    assert [norm.id for norm in norms] == [32237, 41566]
    assert norms[0].issuing_body is None
    assert norms[0].documents[0].url is None


@respx.mock
async def test_same_number_and_year_can_match_two_different_decrees() -> None:
    respond_with_fixture(f"{DECRETO_40_URL}&anio=2022", "decreto_40_2022.json")

    norms = await find_norms(BoletinOficialNormType.DECRETO, 40, 2022)

    assert [(norm.id, norm.issuing_body) for norm in norms] == [
        (619608, "Área Jefe de Gobierno"),
        (667325, "Legislatura de la Ciudad de Buenos Aires"),
    ]


@respx.mock
async def test_repeated_norm_is_returned_once() -> None:
    respond_with_fixture(f"{DECRETO_40_URL}&anio=2025", "decreto_40_2025.json")

    norms = await find_norms(BoletinOficialNormType.DECRETO, 40, 2025)

    assert [norm.id for norm in norms] == [868869]


@respx.mock
async def test_keeps_only_norms_of_the_requested_type_number_and_year() -> None:
    # Respuesta real sin el filtro de año: 17 decretos N° 40 de distintos años.
    respond_with_fixture(f"{DECRETO_40_URL}&anio=2019", "decreto_40_sin_anio.json")

    norms = await find_norms(BoletinOficialNormType.DECRETO, 40, 2019)

    assert [norm.id for norm in norms] == [438789]


@respx.mock
async def test_ignores_norms_of_another_type() -> None:
    # Se pide una ley, pero la respuesta trae un decreto.
    respond_with_fixture(f"{RESULTS_URL}/tipoNorma=1&nNorma=40&anio=2019", "decreto_40_2019.json")

    assert await find_norms(BoletinOficialNormType.LEY, 40, 2019) == []


@respx.mock
async def test_without_results_returns_empty_list() -> None:
    # Sin resultados, `normas` llega como el número 0 en vez de una lista.
    respond_with_fixture(
        f"{RESULTS_URL}/tipoNorma=1&nNorma=6101&anio=2019", "ley_6101_2019_sin_resultados.json"
    )

    assert await find_norms(BoletinOficialNormType.LEY, 6101, 2019) == []


@respx.mock
async def test_invalid_search_criteria_html_raises_error() -> None:
    respond_with_fixture(LEY_6101_2018_URL, "criterio_invalido.html", HTML)

    with pytest.raises(BoletinOficialError):
        await find_norms(BoletinOficialNormType.LEY, 6101, 2018)


@respx.mock
async def test_timeout_raises_error() -> None:
    respx.get(LEY_6101_2018_URL).mock(side_effect=httpx.ReadTimeout("timeout"))

    with pytest.raises(BoletinOficialError):
        await find_norms(BoletinOficialNormType.LEY, 6101, 2018)


@respx.mock
async def test_server_error_raises_error() -> None:
    respx.get(LEY_6101_2018_URL).respond(503, text="Service Unavailable")

    with pytest.raises(BoletinOficialError):
        await find_norms(BoletinOficialNormType.LEY, 6101, 2018)


@respx.mock
async def test_non_json_body_raises_error() -> None:
    respx.get(LEY_6101_2018_URL).respond(
        200, text="<html>Mantenimiento</html>", headers={"Content-Type": HTML}
    )

    with pytest.raises(BoletinOficialError):
        await find_norms(BoletinOficialNormType.LEY, 6101, 2018)


@respx.mock
async def test_unexpected_json_raises_error() -> None:
    respx.get(LEY_6101_2018_URL).respond(200, json={"normas": [{"id": "x"}]})

    with pytest.raises(BoletinOficialError):
        await find_norms(BoletinOficialNormType.LEY, 6101, 2018)
