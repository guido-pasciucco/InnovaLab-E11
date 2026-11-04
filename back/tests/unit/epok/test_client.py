from pathlib import Path

import httpx
import pytest
import respx

from conco.config import settings
from conco.integrations.epok.client import (
    COMMUNE_OFFICES_CATEGORY,
    EpokError,
    find_nearby,
    get_object,
)

pytestmark = pytest.mark.anyio

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures" / "epok"
NEARBY_URL = f"{settings.epok_base_url}/reverseGeocoderLugares/"
OBJECT_URL = f"{settings.epok_base_url}/getObjectContent/"

# Content-Type que EPOK declaró en todas las respuestas reales guardadas en las fixtures.
JAVASCRIPT = "text/javascript"

LONGITUDE = -58.4021372
LATITUDE = -34.6047137


def respond_with_fixture(url: str, name: str) -> respx.Route:
    """Simula EPOK devolviendo una respuesta real guardada en tests/fixtures/epok/."""
    return respx.get(url).respond(
        200,
        content=(FIXTURES_DIR / name).read_bytes(),
        headers={"Content-Type": JAVASCRIPT},
    )


async def find_commune_offices() -> list:
    return await find_nearby(
        longitude=LONGITUDE,
        latitude=LATITUDE,
        categories=[COMMUNE_OFFICES_CATEGORY],
        radius_meters=3000,
    )


@respx.mock
async def test_find_nearby_returns_places_sorted_by_distance() -> None:
    respond_with_fixture(NEARBY_URL, "lugares_cercanos_sedes_de_comunas.json")

    places = await find_commune_offices()

    assert [place.id for place in places] == [
        "sedes_de_comunas|2",
        "sedes_de_comunas|3",
        "sedes_de_comunas|19",
        "sedes_de_comunas|14",
        "sedes_de_comunas|18",
        "sedes_de_comunas|5",
        "sedes_de_comunas|6",
    ]
    assert places[0].name == "Sede Comunal 2"
    assert places[0].distance_meters == 940.95


@respx.mock
async def test_find_nearby_sends_coordinates_category_radius_and_user_agent() -> None:
    route = respond_with_fixture(NEARBY_URL, "lugares_cercanos_sedes_de_comunas.json")

    await find_commune_offices()

    request = route.calls.last.request
    assert dict(request.url.params) == {
        "x": "-58.4021372",
        "y": "-34.6047137",
        "categorias": "sedes_de_comunas",
        "radio": "3000",
    }
    assert request.headers["User-Agent"] == settings.epok_user_agent


@respx.mock
async def test_find_nearby_joins_several_categories_with_commas() -> None:
    route = respond_with_fixture(NEARBY_URL, "lugares_cercanos_sin_resultados.json")

    await find_nearby(
        longitude=LONGITUDE,
        latitude=LATITUDE,
        categories=["sedes_de_comunas", "oficinas_de_empleo"],
        radius_meters=3000,
    )

    params = route.calls.last.request.url.params
    assert params["categorias"] == "sedes_de_comunas,oficinas_de_empleo"


@respx.mock
async def test_find_nearby_without_results_returns_an_empty_list() -> None:
    respond_with_fixture(NEARBY_URL, "lugares_cercanos_sin_resultados.json")

    assert await find_commune_offices() == []


@respx.mock
async def test_get_object_parses_its_content() -> None:
    route = respond_with_fixture(OBJECT_URL, "contenido_sedes_de_comunas_5.json")

    content = await get_object("sedes_de_comunas|5")

    assert content is not None
    assert content.value("nombre") == "Sede Comunal 3"
    assert content.value("direccion") == "SARANDI 1273"
    assert content.value("telefonos") == "4304-5153"
    assert content.value("barrio") == "SAN CRISTOBAL"
    assert content.value("comuna") == "Comuna 3"
    assert content.value("observaciones") is None
    assert content.value("no_existe") is None
    assert content.last_modified == "2024-04-11"
    request = route.calls.last.request
    assert dict(request.url.params) == {"id": "sedes_de_comunas|5"}
    assert request.headers["User-Agent"] == settings.epok_user_agent


@respx.mock
async def test_get_object_unknown_id_returns_none() -> None:
    respond_with_fixture(OBJECT_URL, "contenido_inexistente.json")

    assert await get_object("sedes_de_comunas|99999") is None


@pytest.mark.parametrize("body", [b"", b"<html>error</html>", b'{"foo": 1}'])
@respx.mock
async def test_unexpected_body_raises_epok_error(body: bytes) -> None:
    respx.get(NEARBY_URL).respond(200, content=body, headers={"Content-Type": JAVASCRIPT})
    respx.get(OBJECT_URL).respond(200, content=body, headers={"Content-Type": JAVASCRIPT})

    with pytest.raises(EpokError):
        await find_commune_offices()

    with pytest.raises(EpokError):
        await get_object("sedes_de_comunas|5")


@respx.mock
async def test_server_error_raises_epok_error() -> None:
    respx.get(NEARBY_URL).respond(500, text="Internal Server Error")
    respx.get(OBJECT_URL).respond(503, text="Service Unavailable")

    with pytest.raises(EpokError):
        await find_commune_offices()

    with pytest.raises(EpokError):
        await get_object("sedes_de_comunas|5")


@respx.mock
async def test_timeout_and_dropped_connection_raise_epok_error() -> None:
    respx.get(NEARBY_URL).mock(side_effect=httpx.ReadTimeout("timeout"))
    respx.get(OBJECT_URL).mock(
        side_effect=httpx.RemoteProtocolError("Server disconnected without sending a response.")
    )

    with pytest.raises(EpokError):
        await find_commune_offices()

    with pytest.raises(EpokError):
        await get_object("sedes_de_comunas|5")
