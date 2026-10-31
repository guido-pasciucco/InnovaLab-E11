import pytest

from conco.integrations.epok.client import COMMUNE_OFFICES_CATEGORY, find_nearby, get_object

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def test_nearby_commune_offices_and_their_content_against_real_epok() -> None:
    places = await find_nearby(
        longitude=-58.4021372,
        latitude=-34.6047137,
        categories=[COMMUNE_OFFICES_CATEGORY],
        radius_meters=3000,
    )

    assert places
    distances = [place.distance_meters for place in places]
    assert distances == sorted(distances)
    assert all(place.id.startswith("sedes_de_comunas|") for place in places)

    content = await get_object(places[0].id)

    assert content is not None
    assert content.value("nombre")
    assert content.value("direccion")
    assert await get_object("sedes_de_comunas|99999") is None
