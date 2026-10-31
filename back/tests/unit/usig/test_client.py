from pathlib import Path

import httpx
import pytest
import respx

from conco.config import settings
from conco.integrations.usig.client import (
    UsigError,
    get_datos_utiles_by_address,
    get_datos_utiles_by_coordinates,
)

pytestmark = pytest.mark.anyio

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures" / "usig"
DATOS_UTILES_URL = f"{settings.usig_base_url}/datos_utiles"

# Content-Type que USIG declaró en cada respuesta real guardada en las fixtures.
JAVASCRIPT = "text/javascript; charset=utf-8"
JSON = "application/json; charset=utf-8"
PLAIN_TEXT = "text/plain; charset=utf-8"
HTML = "text/html; charset=utf-8"


def read_fixture(name: str) -> bytes:
    """Lee una respuesta real de USIG guardada en tests/fixtures/usig/, byte a byte."""
    return (FIXTURES_DIR / name).read_bytes()


def respond_with_fixture(name: str, content_type: str) -> respx.Route:
    """Simula USIG devolviendo una respuesta real con el Content-Type que declaró."""
    return respx.get(DATOS_UTILES_URL).respond(
        200, content=read_fixture(name), headers={"Content-Type": content_type}
    )


@respx.mock
async def test_by_address_parses_commune_neighborhood_and_postal_codes() -> None:
    respond_with_fixture("datos_utiles_corrientes_2500.json", JAVASCRIPT)

    result = await get_datos_utiles_by_address("Corrientes", 2500)

    assert result is not None
    assert result.commune == "Comuna 3"
    assert result.neighborhood == "Balvanera"
    assert result.postal_code == "1046"
    assert result.argentine_postal_code == "C1046AAP"


@respx.mock
async def test_by_address_sends_street_and_number() -> None:
    route = respond_with_fixture("datos_utiles_corrientes_2500.json", JAVASCRIPT)

    await get_datos_utiles_by_address("  Corrientes   ", 2500)

    params = route.calls.last.request.url.params
    assert dict(params) == {"calle": "Corrientes", "altura": "2500"}


@respx.mock
async def test_by_address_unknown_street_returns_none() -> None:
    respond_with_fixture("datos_utiles_calle_inexistente.txt", PLAIN_TEXT)

    assert await get_datos_utiles_by_address("Calle Inexistente Xyz", 1234) is None


@respx.mock
async def test_by_coordinates_parses_the_result_without_postal_codes() -> None:
    respond_with_fixture("datos_utiles_coordenadas_corrientes_2500.json", JSON)

    result = await get_datos_utiles_by_coordinates(longitude=-58.401981, latitude=-34.604792)

    assert result is not None
    assert result.commune == "Comuna 3"
    assert result.neighborhood == "Balvanera"
    assert result.postal_code is None
    assert result.argentine_postal_code is None


@respx.mock
async def test_by_coordinates_sends_longitude_as_x_and_latitude_as_y() -> None:
    route = respond_with_fixture("datos_utiles_coordenadas_corrientes_2500.json", JSON)

    await get_datos_utiles_by_coordinates(longitude=-58.401981, latitude=-34.604792)

    params = route.calls.last.request.url.params
    assert dict(params) == {"x": "-58.401981", "y": "-34.604792"}


@respx.mock
async def test_by_coordinates_outside_caba_returns_none() -> None:
    respond_with_fixture("datos_utiles_coordenadas_fuera_de_caba.json", JSON)

    result = await get_datos_utiles_by_coordinates(longitude=-58.7567541, latitude=-34.6423652)

    assert result is None


@respx.mock
async def test_help_page_raises_usig_error() -> None:
    respond_with_fixture("datos_utiles_sin_parametros.html", HTML)

    with pytest.raises(UsigError):
        await get_datos_utiles_by_address("Corrientes", 2500)


@respx.mock
async def test_unexpected_json_raises_usig_error() -> None:
    respx.get(DATOS_UTILES_URL).respond(200, json={"foo": 1})

    with pytest.raises(UsigError):
        await get_datos_utiles_by_coordinates(longitude=-58.4, latitude=-34.6)


@respx.mock
async def test_server_error_raises_usig_error() -> None:
    respx.get(DATOS_UTILES_URL).respond(500, text="Internal Server Error")

    with pytest.raises(UsigError):
        await get_datos_utiles_by_address("Corrientes", 2500)


@respx.mock
async def test_timeout_raises_usig_error() -> None:
    respx.get(DATOS_UTILES_URL).mock(side_effect=httpx.ReadTimeout("timeout"))

    with pytest.raises(UsigError):
        await get_datos_utiles_by_coordinates(longitude=-58.4, latitude=-34.6)
