"""S14: clientes nuevos para normalizar una dirección y resolver su parcela."""

import json
from pathlib import Path
from typing import Any

import pytest
import respx

from conco.config import settings
from conco.integrations.usig import client as usig_client

pytestmark = pytest.mark.anyio

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures" / "usig"
NORMALIZE_URL = "https://servicios.usig.buenosaires.gob.ar/normalizar/"
CATASTRO_API_PARCELA_URL = (
    "https://datosabiertos-catastro-apis.buenosaires.gob.ar/catastro/parcela/"
)


def load_fixture(name: str) -> Any:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def test_the_two_official_base_urls_are_configured() -> None:
    assert settings.usig_normalize_base_url == "https://servicios.usig.buenosaires.gob.ar"
    assert (
        settings.usig_catastro_api_base_url
        == "https://datosabiertos-catastro-apis.buenosaires.gob.ar"
    )


@respx.mock
async def test_normalize_address_parses_the_official_payload() -> None:
    normalize = respx.get(NORMALIZE_URL).respond(
        200, json=load_fixture("normalizar_corrientes.json")
    )

    result = await usig_client.normalize_address("CORRIENTES 2801")

    assert normalize.called
    params = normalize.calls.last.request.url.params
    assert params["direccion"] == "CORRIENTES 2801"
    assert params["geocodificar"] == "true"
    assert params["srid"] == "4326"
    assert len(result) == 1
    item = result[0]
    assert item.street_code == 3174
    assert item.number == 2801
    assert item.partido == "caba"
    assert item.address == "CORRIENTES AV. 2801"


@respx.mock
async def test_normalize_address_returns_an_empty_list_for_an_unknown_street() -> None:
    respx.get(NORMALIZE_URL).respond(
        200, json=load_fixture("normalizar_calle_inexistente.json")
    )

    assert await usig_client.normalize_address("JUANA DE IBARBOUROU 123") == []


@respx.mock
async def test_get_parcela_by_address_uses_the_catastro_api_and_the_normalized_codes() -> None:
    parcela = respx.get(CATASTRO_API_PARCELA_URL).respond(
        200, json=load_fixture("parcela_corrientes.json")
    )

    result = await usig_client.get_parcela_by_address(3174, 2801)

    assert parcela.called
    params = parcela.calls.last.request.url.params
    assert params["codigo_calle"] == "3174"
    assert params["altura"] == "2801"
    assert params["geocodificar"] == "true"
    assert params["srid"] == "4326"
    assert result is not None
    assert result.smp == "013-099-018"
    assert result.address == "CORRIENTES AV. 2801"


@respx.mock
async def test_get_parcela_by_address_without_smp_returns_none() -> None:
    respx.get(CATASTRO_API_PARCELA_URL).respond(200, json={})

    assert await usig_client.get_parcela_by_address(3174, 2801) is None


@respx.mock
async def test_the_new_endpoints_send_a_non_curl_user_agent_and_trailing_slash() -> None:
    normalize = respx.get(NORMALIZE_URL).respond(
        200, json=load_fixture("normalizar_corrientes.json")
    )
    parcela = respx.get(CATASTRO_API_PARCELA_URL).respond(
        200, json=load_fixture("parcela_corrientes.json")
    )

    await usig_client.normalize_address("CORRIENTES 2801")
    await usig_client.get_parcela_by_address(3174, 2801)

    for route in (normalize, parcela):
        assert route.called
        request = route.calls.last.request
        assert request.url.path.endswith("/")
        agent = request.headers["user-agent"]
        assert agent == "CONCO/0.1"
        assert not agent.lower().startswith("curl")


@respx.mock
async def test_repeated_normalize_address_is_served_from_the_usig_cache() -> None:
    normalize = respx.get(NORMALIZE_URL).respond(
        200, json=load_fixture("normalizar_corrientes.json")
    )

    first = await usig_client.normalize_address("CORRIENTES 2801")
    second = await usig_client.normalize_address("CORRIENTES 2801")

    assert first == second
    assert len(normalize.calls) == 1


@respx.mock
async def test_repeated_parcela_by_address_is_served_from_the_usig_cache() -> None:
    parcela = respx.get(CATASTRO_API_PARCELA_URL).respond(
        200, json=load_fixture("parcela_corrientes.json")
    )

    first = await usig_client.get_parcela_by_address(3174, 2801)
    second = await usig_client.get_parcela_by_address(3174, 2801)

    assert first == second
    assert len(parcela.calls) == 1
