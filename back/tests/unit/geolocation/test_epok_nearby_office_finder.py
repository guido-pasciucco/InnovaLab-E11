from pathlib import Path

import httpx
import pytest
import respx

from conco.config import settings
from conco.geolocation.domain import NearbyOffice, NearbyOfficeError, Source
from conco.geolocation.infrastructure import EpokNearbyOfficeFinder, extract_link

pytestmark = pytest.mark.anyio

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures" / "epok"
NEARBY_URL = f"{settings.epok_base_url}/reverseGeocoderLugares/"
OBJECT_URL = f"{settings.epok_base_url}/getObjectContent/"
COMMUNE_2_URL = (
    "https://buenosaires.gob.ar/jefaturadegabinete/atencion-ciudadana-y-gestion-comunal/"
    "gestion-comunal/comuna-2"
)
COMMUNE_3_URL = (
    "https://buenosaires.gob.ar/jefaturadegabinete/atencion-ciudadana-y-gestion-comunal/"
    "gestion-comunal/comuna-3"
)

LATITUDE = -34.6047137
LONGITUDE = -58.4021372


def fixture(name: str) -> bytes:
    return (FIXTURES_DIR / name).read_bytes()


def mock_nearby(name: str = "lugares_cercanos_sedes_de_comunas.json") -> respx.Route:
    """Simula `reverseGeocoderLugares` con una respuesta real guardada."""
    return respx.get(NEARBY_URL).respond(
        200, content=fixture(name), headers={"Content-Type": "text/javascript"}
    )


def mock_object(object_id: str, name: str) -> respx.Route:
    """Simula `getObjectContent` de un lugar con una respuesta real guardada."""
    return respx.get(OBJECT_URL, params={"id": object_id}).respond(
        200, content=fixture(name), headers={"Content-Type": "text/javascript"}
    )


def mock_three_closest_objects() -> None:
    mock_object("sedes_de_comunas|2", "contenido_sedes_de_comunas_2.json")
    mock_object("sedes_de_comunas|3", "contenido_sedes_de_comunas_3.json")
    mock_object("sedes_de_comunas|19", "contenido_sedes_de_comunas_19.json")


def test_source_cites_epok() -> None:
    assert EpokNearbyOfficeFinder().source == Source(
        name="USIG - EPOK (Gobierno de la Ciudad de Buenos Aires)",
        url="https://epok.buenosaires.gob.ar",
        license=(
            "Sin licencia explícita; se asume Creative Commons Reconocimiento 2.5 Argentina "
            "(CC BY 2.5 AR), como el resto de los datos de la Ciudad"
        ),
    )


@respx.mock
async def test_maps_the_closest_offices_sorted_by_distance() -> None:
    nearby = mock_nearby()
    mock_three_closest_objects()

    offices = await EpokNearbyOfficeFinder().find_nearby(
        latitude=LATITUDE, longitude=LONGITUDE, limit=3
    )

    assert offices == [
        NearbyOffice(
            name="Sede Comunal 2",
            address="URIBURU JOSE E., Pres. 1022",
            phone="4370-9702",
            neighborhood="RECOLETA",
            commune="Comuna 2",
            distance_meters=940.95,
            info_url=COMMUNE_2_URL,
            last_updated="2024-04-11",
        ),
        NearbyOffice(
            name="Subsede Comunal 3",
            address="MORENO 2301",
            phone="4304-5153",
            neighborhood="BALVANERA",
            commune="Comuna 3",
            distance_meters=962.53,
            info_url=COMMUNE_3_URL,
            last_updated="2024-04-11",
        ),
        NearbyOffice(
            name="Subsede Comunal 2",
            address="LOPEZ, VICENTE 2050 3 piso",
            phone="4808-7300",
            neighborhood="RECOLETA",
            commune="Comuna 2",
            distance_meters=1893.33,
            info_url=COMMUNE_2_URL,
            last_updated="2024-04-11",
        ),
    ]
    assert dict(nearby.calls.last.request.url.params) == {
        "x": "-58.4021372",
        "y": "-34.6047137",
        "categorias": "sedes_de_comunas",
        "radio": str(settings.epok_radius_meters),
    }


@respx.mock
async def test_only_fetches_the_content_of_the_requested_number_of_offices() -> None:
    mock_nearby()
    closest = mock_object("sedes_de_comunas|2", "contenido_sedes_de_comunas_2.json")
    others = respx.get(OBJECT_URL).respond(500)

    offices = await EpokNearbyOfficeFinder().find_nearby(
        latitude=LATITUDE, longitude=LONGITUDE, limit=1
    )

    assert [office.name for office in offices] == ["Sede Comunal 2"]
    assert closest.call_count == 1
    assert others.call_count == 0


@respx.mock
async def test_skips_an_office_without_content() -> None:
    mock_nearby()
    mock_object("sedes_de_comunas|2", "contenido_sedes_de_comunas_2.json")
    mock_object("sedes_de_comunas|3", "contenido_inexistente.json")
    mock_object("sedes_de_comunas|19", "contenido_sedes_de_comunas_19.json")

    offices = await EpokNearbyOfficeFinder().find_nearby(
        latitude=LATITUDE, longitude=LONGITUDE, limit=3
    )

    assert [office.name for office in offices] == ["Sede Comunal 2", "Subsede Comunal 2"]


@respx.mock
async def test_nothing_in_range_returns_an_empty_list_without_fetching_content() -> None:
    mock_nearby("lugares_cercanos_sin_resultados.json")
    content = respx.get(OBJECT_URL).respond(500)

    offices = await EpokNearbyOfficeFinder().find_nearby(
        latitude=LATITUDE, longitude=LONGITUDE, limit=3
    )

    assert offices == []
    assert content.call_count == 0


@respx.mock
async def test_nearby_search_failure_raises_nearby_office_error() -> None:
    respx.get(NEARBY_URL).mock(side_effect=httpx.ReadTimeout("timeout"))

    with pytest.raises(NearbyOfficeError):
        await EpokNearbyOfficeFinder().find_nearby(
            latitude=LATITUDE, longitude=LONGITUDE, limit=3
        )


@respx.mock
async def test_content_failure_raises_nearby_office_error() -> None:
    mock_nearby()
    respx.get(OBJECT_URL).respond(502, text="Bad Gateway")

    with pytest.raises(NearbyOfficeError):
        await EpokNearbyOfficeFinder().find_nearby(
            latitude=LATITUDE, longitude=LONGITUDE, limit=3
        )


@pytest.mark.parametrize(
    ("html", "expected"),
    [
        (
            '<a href="https://buenosaires.gob.ar/comuna-3" target="_blank">Página web</a>',
            "https://buenosaires.gob.ar/comuna-3",
        ),
        ('<a href="http://example.org/a">x</a><a href="https://b">y</a>', "http://example.org/a"),
        ("Página web", None),
        ('<a href="javascript:alert(1)">x</a>', None),
        ('<a name="sin-enlace">x</a>', None),
        (None, None),
    ],
)
def test_extract_link_returns_the_first_web_link(html: str | None, expected: str | None) -> None:
    assert extract_link(html) == expected
