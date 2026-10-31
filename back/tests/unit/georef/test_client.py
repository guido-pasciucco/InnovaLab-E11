import json
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from conco.config import settings
from conco.integrations.georef.client import (
    GeorefError,
    normalize_address,
    search_addresses,
)

pytestmark = pytest.mark.anyio

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures" / "georef"
ADDRESSES_URL = f"{settings.georef_base_url}/direcciones"


def load_fixture(name: str) -> Any:
    """Lee una respuesta real de Georef guardada en tests/fixtures/georef/."""
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def test_normalize_address_removes_extra_spaces() -> None:
    assert normalize_address("  Corrientes   2500 ") == "Corrientes 2500"


@respx.mock
async def test_search_addresses_parses_a_full_result() -> None:
    respx.get(ADDRESSES_URL).respond(
        200, json=load_fixture("direcciones_corrientes_2500.json")
    )

    result = await search_addresses("Corrientes 2500")

    assert result.count == 1
    address = result.addresses[0]
    assert address.nomenclature.startswith("AV CORRIENTES 2500")
    assert address.department.name == "Comuna 3"
    assert address.height.value == 2500
    assert address.location is not None
    assert address.location.lat == pytest.approx(-34.6047137500375)
    assert address.location.lon == pytest.approx(-58.402137170712)


@respx.mock
async def test_search_addresses_sends_normalized_query_params() -> None:
    route = respx.get(ADDRESSES_URL).respond(
        200, json=load_fixture("direcciones_corrientes_2500.json")
    )

    await search_addresses("  Corrientes   2500 ")

    params = route.calls.last.request.url.params
    assert params["direccion"] == "Corrientes 2500"
    assert params["provincia"] == "caba"
    assert params["max"] == "5"


@respx.mock
async def test_search_addresses_without_results_returns_empty_list() -> None:
    respx.get(ADDRESSES_URL).respond(
        200, json=load_fixture("direcciones_sin_resultados.json")
    )

    result = await search_addresses("Calle Inventada Xyz 9999")

    assert result.count == 0
    assert result.addresses == []


@respx.mock
async def test_search_addresses_street_without_number_has_no_height() -> None:
    respx.get(ADDRESSES_URL).respond(
        200, json=load_fixture("direcciones_sin_altura.json")
    )

    result = await search_addresses("Corrientes")

    address = result.addresses[0]
    assert address.height.value is None
    assert address.location is not None


@respx.mock
async def test_search_addresses_http_error_raises_georef_error() -> None:
    respx.get(ADDRESSES_URL).respond(
        400, json=load_fixture("error_400_falta_direccion.json")
    )

    with pytest.raises(GeorefError):
        await search_addresses("")


@respx.mock
async def test_search_addresses_timeout_raises_georef_error() -> None:
    respx.get(ADDRESSES_URL).mock(side_effect=httpx.ConnectTimeout("timeout"))

    with pytest.raises(GeorefError):
        await search_addresses("Corrientes 2500")


@respx.mock
async def test_search_addresses_unexpected_payload_raises_georef_error() -> None:
    respx.get(ADDRESSES_URL).respond(200, json={"foo": 1})

    with pytest.raises(GeorefError):
        await search_addresses("Corrientes 2500")


@respx.mock
async def test_search_addresses_non_json_body_raises_georef_error() -> None:
    respx.get(ADDRESSES_URL).respond(200, text="<html>Mantenimiento</html>")

    with pytest.raises(GeorefError):
        await search_addresses("Corrientes 2500")
