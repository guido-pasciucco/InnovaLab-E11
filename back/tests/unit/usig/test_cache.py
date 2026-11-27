"""S8: caché TTL/LRU del cliente USIG, sólo para respuestas exitosas."""

import asyncio

import httpx
import pytest
import respx

from conco.config import settings
from conco.integrations.usig import client as usig_client
from conco.territory.infrastructure import UsigTerritoryService

pytestmark = pytest.mark.anyio

BASE = settings.usig_base_url
PARCELA_URL = f"{BASE}/catastro/parcela/"
MIXTURA_URL = f"{BASE}/cur3d/mixtura_usos/"
CATEGORIAS_URL = f"{BASE}/cur3d/categorias/"
RUBROS_URL = f"{BASE}/cur3d/cuadrosdeuso/rubros/"


def test_cache_settings_have_the_documented_defaults() -> None:
    assert settings.usig_cache_ttl_seconds == 300.0
    assert settings.usig_cache_max_entries == 256


@respx.mock
async def test_a_cache_hit_avoids_a_second_upstream_call() -> None:
    route = respx.get(PARCELA_URL).respond(
        200, json={"smp": "013-099-018", "direccion": "CORRIENTES AV. 2801"}
    )

    first = await usig_client.get_parcela(-34.6040, -58.4055)
    second = await usig_client.get_parcela(-34.6040, -58.4055)

    assert first == second
    assert second.smp == "013-099-018"
    assert len(route.calls) == 1


@respx.mock
async def test_an_expired_entry_is_a_miss(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "usig_cache_ttl_seconds", 0.01)
    route = respx.get(PARCELA_URL).respond(200, json={"smp": "013-099-018"})

    await usig_client.get_parcela(-34.6040, -58.4055)
    await asyncio.sleep(0.03)
    await usig_client.get_parcela(-34.6040, -58.4055)

    assert len(route.calls) == 2


@respx.mock
async def test_lru_eviction_drops_the_least_recently_used(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "usig_cache_max_entries", 2)
    route = respx.get(MIXTURA_URL).respond(200, json={"usos": [4, 0, 0]})

    await usig_client.get_mix_area("A")  # miss 1
    await usig_client.get_mix_area("B")  # miss 2
    await usig_client.get_mix_area("A")  # hit: A pasa a ser la más reciente
    await usig_client.get_mix_area("C")  # miss 3: expulsa B
    await usig_client.get_mix_area("B")  # miss 4: B había sido expulsada

    assert len(route.calls) == 4


@respx.mock
async def test_http_errors_are_never_cached() -> None:
    route = respx.get(PARCELA_URL).mock(
        side_effect=[
            httpx.Response(500, text="down"),
            httpx.Response(
                200, json={"smp": "013-099-018", "direccion": "CORRIENTES AV. 2801"}
            ),
        ]
    )

    with pytest.raises(usig_client.UsigError):
        await usig_client.get_parcela(-34.6040, -58.4055)
    result = await usig_client.get_parcela(-34.6040, -58.4055)

    assert result.smp == "013-099-018"
    assert len(route.calls) == 2


@respx.mock
async def test_parse_errors_are_never_cached() -> None:
    route = respx.get(MIXTURA_URL).mock(
        side_effect=[
            httpx.Response(200, text="esto no es JSON"),
            httpx.Response(200, json={"usos": [4, 0, 0]}),
        ]
    )

    with pytest.raises(usig_client.UsigError):
        await usig_client.get_mix_area("013-099-018")
    assert await usig_client.get_mix_area("013-099-018") == 4
    assert len(route.calls) == 2


@respx.mock
async def test_clear_usig_cache_forces_a_fresh_upstream_call() -> None:
    route = respx.get(MIXTURA_URL).respond(200, json={"usos": [4, 0, 0]})

    await usig_client.get_mix_area("013-099-018")
    usig_client.clear_usig_cache()
    await usig_client.get_mix_area("013-099-018")

    assert len(route.calls) == 2


@respx.mock
async def test_concurrent_use_table_calls_still_work() -> None:
    respx.get(PARCELA_URL).respond(
        200, json={"smp": "013-099-018", "direccion": "CORRIENTES AV. 2801"}
    )
    respx.get(MIXTURA_URL).respond(200, json={"usos": [4, 0, 0]})
    respx.get(CATEGORIAS_URL).respond(200, json=[{"id": 1, "nombre": "Comercial"}])
    respx.get(RUBROS_URL).respond(
        200, json={"rubros": [{"rubro_id": 102, "rubro": "Alimentación"}]}
    )

    first, second = await asyncio.gather(
        UsigTerritoryService().resolve_use_table(-34.6040, -58.4055),
        UsigTerritoryService().resolve_use_table(-34.6040, -58.4055),
    )

    assert first.smp == second.smp == "013-099-018"
    assert first.mix_area == second.mix_area == 4
    assert len(first.categories) == len(second.categories) == 1
