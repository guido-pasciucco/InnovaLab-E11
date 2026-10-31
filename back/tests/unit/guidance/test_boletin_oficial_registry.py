from datetime import date
from pathlib import Path

import httpx
import pytest
import respx

from conco.config import settings
from conco.guidance.domain import Regulation, RegulationLookupError, RegulationType, Source
from conco.guidance.infrastructure import BoletinOficialRegulationRegistry

pytestmark = pytest.mark.anyio

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures" / "boletin_oficial"
RESULTS_URL = f"{settings.boletin_oficial_base_url}/obtenerResultado"


def respond_with_fixture(path: str, name: str) -> respx.Route:
    """Simula el Boletín Oficial devolviendo una respuesta real guardada en las fixtures."""
    return respx.get(f"{RESULTS_URL}/{path}").respond(
        200,
        content=(FIXTURES_DIR / name).read_bytes(),
        headers={"Content-Type": "application/json"},
    )


def test_source_cites_the_official_bulletin() -> None:
    assert BoletinOficialRegulationRegistry().source == Source(
        name="Boletín Oficial de la Ciudad de Buenos Aires",
        url="https://boletinoficial.buenosaires.gob.ar",
        license=(
            "Sin licencia explícita: normas oficiales de publicación obligatoria y acceso "
            "público"
        ),
    )


@respx.mock
async def test_find_maps_a_law_to_the_domain() -> None:
    route = respond_with_fixture("tipoNorma=1&nNorma=6101&anio=2018", "ley_6101_2018.json")

    regulations = await BoletinOficialRegulationRegistry().find(RegulationType.LEY, 6101, 2018)

    assert route.called
    assert regulations == [
        Regulation(
            type=RegulationType.LEY,
            number=6101,
            year=2018,
            summary=(
                "Ley Marco de Regulación de actividades económicas de la Ciudad Autónoma de "
                "Buenos Aires"
            ),
            issuing_body="Legislatura de la Ciudad de Buenos Aires",
            publication_date=date(2018, 12, 27),
            bulletin_number=5526,
            document_url="https://api-restboletinoficial.buenosaires.gob.ar/download/1255476",
        )
    ]


@respx.mock
async def test_find_maps_a_decree_using_the_decree_type_id() -> None:
    route = respond_with_fixture("tipoNorma=2&nNorma=40&anio=2019", "decreto_40_2019.json")

    regulations = await BoletinOficialRegulationRegistry().find(RegulationType.DECRETO, 40, 2019)

    assert route.called
    assert [(r.type, r.number, r.year, r.bulletin_number) for r in regulations] == [
        (RegulationType.DECRETO, 40, 2019, 5538)
    ]


@respx.mock
async def test_find_keeps_every_norm_sharing_number_and_year() -> None:
    respond_with_fixture("tipoNorma=2&nNorma=40&anio=2022", "decreto_40_2022.json")

    regulations = await BoletinOficialRegulationRegistry().find(RegulationType.DECRETO, 40, 2022)

    assert [r.issuing_body for r in regulations] == [
        "Área Jefe de Gobierno",
        "Legislatura de la Ciudad de Buenos Aires",
    ]


@respx.mock
async def test_find_old_norm_without_document_link_or_issuing_body() -> None:
    respond_with_fixture("tipoNorma=2&nNorma=40&anio=2010", "decreto_40_2010.json")

    regulations = await BoletinOficialRegulationRegistry().find(RegulationType.DECRETO, 40, 2010)

    assert regulations[0].issuing_body is None
    assert regulations[0].document_url is None
    assert regulations[0].publication_date == date(2010, 1, 15)


@respx.mock
async def test_find_unknown_norm_returns_empty_list() -> None:
    respond_with_fixture(
        "tipoNorma=1&nNorma=6101&anio=2019", "ley_6101_2019_sin_resultados.json"
    )

    assert await BoletinOficialRegulationRegistry().find(RegulationType.LEY, 6101, 2019) == []


@respx.mock
async def test_find_translates_client_errors_to_domain_errors() -> None:
    respx.get(f"{RESULTS_URL}/tipoNorma=1&nNorma=6101&anio=2018").mock(
        side_effect=httpx.ConnectTimeout("timeout")
    )

    with pytest.raises(RegulationLookupError):
        await BoletinOficialRegulationRegistry().find(RegulationType.LEY, 6101, 2018)
