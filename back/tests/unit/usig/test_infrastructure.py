import json
from pathlib import Path
from typing import Any

import pytest
import respx

from conco.config import settings
from conco.territory.domain import TerritoryLookupError
from conco.territory.infrastructure import UsigTerritoryService

pytestmark = pytest.mark.anyio

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures" / "usig"
BASE = settings.usig_base_url
PARCELA_URL = f"{BASE}/catastro/parcela/"
MIXTURA_URL = f"{BASE}/cur3d/mixtura_usos/"
CATEGORIAS_URL = f"{BASE}/cur3d/categorias/"
RUBROS_URL = f"{BASE}/cur3d/cuadrosdeuso/rubros/"
REFERENCIAS_URL = f"{BASE}/cur3d/cuadrosdeuso/referencias/"


def load_fixture(name: str) -> Any:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


@respx.mock
async def test_use_table_calls_one_of_each_plus_ten_rubros() -> None:
    parcela = respx.get(PARCELA_URL).respond(
        200, json=load_fixture("parcela_corrientes.json")
    )
    mixtura = respx.get(MIXTURA_URL).respond(200, json=load_fixture("mixtura_usos.json"))
    categorias = respx.get(CATEGORIAS_URL).respond(
        200, json=load_fixture("categorias.json")
    )
    rubros = respx.get(RUBROS_URL).respond(200, json=load_fixture("rubros.json"))

    result = await UsigTerritoryService().resolve_use_table(-34.6040, -58.4055)

    assert result.smp == "013-099-018"
    assert result.official_address == "CORRIENTES AV. 2801"
    assert result.mix_area == 4
    assert len(result.categories) == 10
    assert all(category.rubros for category in result.categories)
    assert len(parcela.calls) == 1
    assert len(mixtura.calls) == 1
    assert len(categorias.calls) == 1
    assert len(rubros.calls) == 10
    assert [call.request.url.params["categoria"] for call in rubros.calls] == [
        str(value) for value in range(1, 11)
    ]
    assert all(call.request.url.params["mixtura"] == "4" for call in rubros.calls)


@respx.mock
async def test_empty_parcela_skips_all_downstream_calls() -> None:
    respx.get(PARCELA_URL).respond(200, json=load_fixture("parcela_vacia.json"))
    mixtura = respx.get(MIXTURA_URL).respond(200, json=load_fixture("mixtura_usos.json"))
    categorias = respx.get(CATEGORIAS_URL).respond(
        200, json=load_fixture("categorias.json")
    )
    rubros = respx.get(RUBROS_URL).respond(200, json=load_fixture("rubros.json"))

    result = await UsigTerritoryService().resolve_use_table(-34.5000, -58.4000)

    assert result.smp is None
    assert result.official_address is None
    assert result.mix_area is None
    assert result.categories == []
    assert any("parcela" in item.lower() for item in result.limitations)
    assert not mixtura.called
    assert not categorias.called
    assert not rubros.called


@respx.mock
async def test_upstream_error_becomes_territory_lookup_error() -> None:
    respx.get(PARCELA_URL).respond(200, json=load_fixture("error_smp_invalido.json"))

    with pytest.raises(TerritoryLookupError):
        await UsigTerritoryService().resolve_use_table(-34.6040, -58.4055)


@respx.mock
async def test_referencias_flattens_details_and_keeps_observaciones() -> None:
    route = respx.get(REFERENCIAS_URL).respond(
        200, json=load_fixture("referencias.json")
    )

    result = await UsigTerritoryService().resolve_references("013-099-018", 1, 4, 102)

    assert result.permitido_mixtura_de_usos == [
        "Permitido en el Área de Mixtura de Usos"
    ]
    assert all(
        isinstance(item, str)
        for item in result.bicicletas + result.estacionamientos + result.cargaydescarga
    )
    assert result.observaciones is not None and "3.6.1.1" in result.observaciones
    params = route.calls.last.request.url.params
    assert params["categoria"] == "1"
    assert params["mixtura"] == "4"
    assert params["rubro"] == "102"


@respx.mock
async def test_referencias_upstream_error_becomes_territory_lookup_error() -> None:
    respx.get(REFERENCIAS_URL).respond(500, text="Internal Server Error")

    with pytest.raises(TerritoryLookupError):
        await UsigTerritoryService().resolve_references("013-099-018", 1, 4, 102)
