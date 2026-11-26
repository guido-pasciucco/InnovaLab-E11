"""S14: fallback por dirección en el adaptador de territorio."""

import json
from pathlib import Path
from typing import Any

import pytest
import respx

from conco.config import settings
from conco.territory import domain as territory_domain
from conco.territory.infrastructure import UsigTerritoryService

pytestmark = pytest.mark.anyio

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures" / "usig"
BASE = settings.usig_base_url
POINT_PARCELA_URL = f"{BASE}/catastro/parcela/"
NORMALIZE_URL = "https://servicios.usig.buenosaires.gob.ar/normalizar/"
CATASTRO_API_PARCELA_URL = (
    "https://datosabiertos-catastro-apis.buenosaires.gob.ar/catastro/parcela/"
)
MIXTURA_URL = f"{BASE}/cur3d/mixtura_usos/"
CATEGORIAS_URL = f"{BASE}/cur3d/categorias/"
RUBROS_URL = f"{BASE}/cur3d/cuadrosdeuso/rubros/"


def load_fixture(name: str) -> Any:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


@respx.mock
async def test_a_point_hit_keeps_the_original_chain_even_when_an_address_is_supplied() -> None:
    parcela = respx.get(POINT_PARCELA_URL).respond(
        200, json=load_fixture("parcela_corrientes.json")
    )
    normalize = respx.get(NORMALIZE_URL).respond(
        200, json=load_fixture("normalizar_corrientes.json")
    )
    respx.get(MIXTURA_URL).respond(200, json=load_fixture("mixtura_usos.json"))
    respx.get(CATEGORIAS_URL).respond(200, json=load_fixture("categorias.json"))
    rubros = respx.get(RUBROS_URL).respond(200, json=load_fixture("rubros.json"))

    result = await UsigTerritoryService().resolve_use_table(
        -34.6040, -58.4055, "CORRIENTES 2801"
    )

    assert result.smp == "013-099-018"
    assert result.official_address == "CORRIENTES AV. 2801"
    assert result.mix_area == 4
    assert len(result.categories) == 10
    assert len(parcela.calls) == 1
    assert not normalize.called
    assert territory_domain.APPROXIMATE_LOCATION_LIMITATION in result.limitations
    assert territory_domain.ADDRESS_RESOLVED_LIMITATION not in result.limitations


@respx.mock
async def test_an_empty_point_with_a_known_address_resolves_the_parcela_by_address() -> None:
    respx.get(POINT_PARCELA_URL).respond(200, json=load_fixture("parcela_vacia.json"))
    normalize = respx.get(NORMALIZE_URL).respond(
        200, json=load_fixture("normalizar_corrientes.json")
    )
    parcela_address = respx.get(CATASTRO_API_PARCELA_URL).respond(
        200, json=load_fixture("parcela_corrientes.json")
    )
    mix = respx.get(MIXTURA_URL).respond(200, json=load_fixture("mixtura_usos.json"))
    respx.get(CATEGORIAS_URL).respond(200, json=load_fixture("categorias.json"))
    rubros = respx.get(RUBROS_URL).respond(200, json=load_fixture("rubros.json"))

    result = await UsigTerritoryService().resolve_use_table(
        -34.5000, -58.4000, "CORRIENTES 2801"
    )

    assert normalize.called
    assert normalize.calls.last.request.url.params["direccion"] == "CORRIENTES 2801"
    assert parcela_address.called
    address_params = parcela_address.calls.last.request.url.params
    assert address_params["codigo_calle"] == "3174"
    assert address_params["altura"] == "2801"
    assert mix.calls.last.request.url.params["smp"] == "013-099-018"
    assert [call.request.url.params["categoria"] for call in rubros.calls] == [
        str(value) for value in range(1, 11)
    ]
    assert all(call.request.url.params["mixtura"] == "4" for call in rubros.calls)
    assert result.smp == "013-099-018"
    assert result.official_address == "CORRIENTES AV. 2801"
    assert result.mix_area == 4
    assert len(result.categories) == 10
    assert territory_domain.ADDRESS_RESOLVED_LIMITATION in result.limitations


@respx.mock
async def test_an_unknown_address_returns_an_empty_result_with_a_clear_limitation() -> None:
    respx.get(POINT_PARCELA_URL).respond(200, json=load_fixture("parcela_vacia.json"))
    respx.get(NORMALIZE_URL).respond(
        200, json=load_fixture("normalizar_calle_inexistente.json")
    )
    parcela_address = respx.get(CATASTRO_API_PARCELA_URL).respond(
        200, json=load_fixture("parcela_corrientes.json")
    )
    mix = respx.get(MIXTURA_URL).respond(200, json=load_fixture("mixtura_usos.json"))

    result = await UsigTerritoryService().resolve_use_table(
        -34.5000, -58.4000, "JUANA DE IBARBOUROU 123"
    )

    assert result.smp is None
    assert result.categories == []
    assert territory_domain.NO_PARCELA_BY_ADDRESS_LIMITATION in result.limitations
    assert any("USIG" in item and "dirección" in item.lower() for item in result.limitations)
    assert not parcela_address.called
    assert not mix.called


@respx.mock
async def test_an_empty_point_without_address_never_normalizes() -> None:
    respx.get(POINT_PARCELA_URL).respond(200, json=load_fixture("parcela_vacia.json"))
    normalize = respx.get(NORMALIZE_URL).respond(
        200, json=load_fixture("normalizar_corrientes.json")
    )

    result = await UsigTerritoryService().resolve_use_table(-34.5000, -58.4000)

    assert result.smp is None
    assert not normalize.called
    assert territory_domain.NO_PARCELA_BY_ADDRESS_LIMITATION not in result.limitations


@respx.mock
async def test_the_fallback_picks_the_first_caba_result_only() -> None:
    respx.get(POINT_PARCELA_URL).respond(200, json=load_fixture("parcela_vacia.json"))
    respx.get(NORMALIZE_URL).respond(
        200,
        json={
            "direccionesNormalizadas": [
                {"altura": 100, "cod_calle": 1111, "cod_partido": "gba", "direccion": "GBA"},
                {
                    "altura": 2801,
                    "cod_calle": 3174,
                    "cod_partido": "caba",
                    "direccion": "CORRIENTES AV. 2801",
                },
            ]
        },
    )
    parcela_address = respx.get(CATASTRO_API_PARCELA_URL).respond(
        200, json=load_fixture("parcela_corrientes.json")
    )
    respx.get(MIXTURA_URL).respond(200, json=load_fixture("mixtura_usos.json"))
    respx.get(CATEGORIAS_URL).respond(200, json=load_fixture("categorias.json"))
    respx.get(RUBROS_URL).respond(200, json=load_fixture("rubros.json"))

    result = await UsigTerritoryService().resolve_use_table(
        -34.5000, -58.4000, "CORRIENTES 2801"
    )

    assert parcela_address.calls.last.request.url.params["codigo_calle"] == "3174"
    assert result.smp == "013-099-018"
