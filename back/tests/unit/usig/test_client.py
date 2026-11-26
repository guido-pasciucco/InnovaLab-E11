import json
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from conco.config import settings
from conco.integrations.usig import client as usig_client

pytestmark = pytest.mark.anyio

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures" / "usig"
BASE = settings.usig_base_url
PARCELA_URL = f"{BASE}/catastro/parcela/"
MIXTURA_URL = f"{BASE}/cur3d/mixtura_usos/"
CATEGORIAS_URL = f"{BASE}/cur3d/categorias/"
RUBROS_URL = f"{BASE}/cur3d/cuadrosdeuso/rubros/"
REFERENCIAS_URL = f"{BASE}/cur3d/cuadrosdeuso/referencias/"


def load_fixture(name: str) -> Any:
    """Lee una respuesta real de USIG guardada en tests/fixtures/usig/."""
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


@respx.mock
async def test_every_upstream_request_sends_a_non_curl_user_agent() -> None:
    routes = [
        respx.get(PARCELA_URL).respond(200, json=load_fixture("parcela_corrientes.json")),
        respx.get(MIXTURA_URL).respond(200, json=load_fixture("mixtura_usos.json")),
        respx.get(CATEGORIAS_URL).respond(200, json=load_fixture("categorias.json")),
        respx.get(RUBROS_URL).respond(200, json=load_fixture("rubros.json")),
        respx.get(REFERENCIAS_URL).respond(200, json=load_fixture("referencias.json")),
    ]

    await usig_client.get_parcela(-34.6040, -58.4055)
    await usig_client.get_mix_area("013-099-018")
    await usig_client.list_categorias()
    await usig_client.list_rubros(1, 4)
    await usig_client.get_referencias(1, 4, 102)

    for route in routes:
        assert route.called
        agent = route.calls.last.request.headers["user-agent"]
        assert agent == "CONCO/0.1"
        assert not agent.lower().startswith("curl")


@respx.mock
async def test_all_upstream_paths_end_with_a_trailing_slash() -> None:
    routes = [
        respx.get(PARCELA_URL).respond(200, json=load_fixture("parcela_corrientes.json")),
        respx.get(MIXTURA_URL).respond(200, json=load_fixture("mixtura_usos.json")),
        respx.get(CATEGORIAS_URL).respond(200, json=load_fixture("categorias.json")),
        respx.get(RUBROS_URL).respond(200, json=load_fixture("rubros.json")),
        respx.get(REFERENCIAS_URL).respond(200, json=load_fixture("referencias.json")),
    ]

    await usig_client.get_parcela(-34.6040, -58.4055)
    await usig_client.get_mix_area("013-099-018")
    await usig_client.list_categorias()
    await usig_client.list_rubros(1, 4)
    await usig_client.get_referencias(1, 4, 102)

    paths = [str(call.request.url.path) for route in routes for call in route.calls]
    assert paths and all(path.endswith("/") for path in paths)


@respx.mock
async def test_successful_chain_parses_the_real_fixtures() -> None:
    respx.get(PARCELA_URL).respond(200, json=load_fixture("parcela_corrientes.json"))
    respx.get(MIXTURA_URL).respond(200, json=load_fixture("mixtura_usos.json"))
    respx.get(CATEGORIAS_URL).respond(200, json=load_fixture("categorias.json"))
    respx.get(RUBROS_URL).respond(200, json=load_fixture("rubros.json"))
    respx.get(REFERENCIAS_URL).respond(200, json=load_fixture("referencias.json"))

    parcela = await usig_client.get_parcela(-34.6040, -58.4055)
    assert parcela.smp == "013-099-018"
    assert parcela.address == "CORRIENTES AV. 2801"
    assert await usig_client.get_mix_area("013-099-018") == 4

    categorias = await usig_client.list_categorias()
    assert len(categorias) == 10
    assert categorias[0].id == 1
    assert categorias[0].name == "Comercial"

    rubros = await usig_client.list_rubros(1, 4)
    assert rubros and all(rubro.id and rubro.name for rubro in rubros)

    referencias = await usig_client.get_referencias(1, 4, 102)
    assert referencias.permitido_mixtura_de_usos[0].detail == (
        "Permitido en el Área de Mixtura de Usos"
    )


@respx.mock
async def test_empty_parcela_maps_to_null_fields() -> None:
    respx.get(PARCELA_URL).respond(200, json=load_fixture("parcela_vacia.json"))

    parcela = await usig_client.get_parcela(-34.5000, -58.4000)

    assert parcela.smp is None
    assert parcela.address is None


@respx.mock
async def test_error_payload_from_upstream_raises_usig_error() -> None:
    respx.get(MIXTURA_URL).respond(200, json=load_fixture("error_smp_invalido.json"))

    with pytest.raises(usig_client.UsigError):
        await usig_client.get_mix_area("SMP-INVALIDO")


@respx.mock
async def test_missing_mixtura_for_invalid_smp_raises_usig_error() -> None:
    respx.get(MIXTURA_URL).respond(200, json=load_fixture("mixtura_usos_vacia.json"))

    with pytest.raises(usig_client.UsigError):
        await usig_client.get_mix_area("000-000-000")


@respx.mock
async def test_timeout_raises_usig_error() -> None:
    respx.get(PARCELA_URL).mock(side_effect=httpx.TimeoutException("timeout"))

    with pytest.raises(usig_client.UsigError):
        await usig_client.get_parcela(-34.6040, -58.4055)


@respx.mock
async def test_network_error_raises_usig_error() -> None:
    respx.get(CATEGORIAS_URL).mock(side_effect=httpx.ConnectError("down"))

    with pytest.raises(usig_client.UsigError):
        await usig_client.list_categorias()
