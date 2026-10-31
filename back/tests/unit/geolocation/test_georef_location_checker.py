import json
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from conco.config import settings
from conco.geolocation.domain import LocationCheck, LocationCheckError
from conco.geolocation.infrastructure import GeorefLocationChecker

pytestmark = pytest.mark.anyio

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures" / "georef"
LOCATION_URL = f"{settings.georef_base_url}/ubicacion"


def load_fixture(name: str) -> Any:
    """Lee una respuesta real de Georef guardada en tests/fixtures/georef/."""
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


@respx.mock
async def test_a_point_in_caba_is_in_caba() -> None:
    respx.get(LOCATION_URL).respond(
        200, json=load_fixture("ubicacion_caba_corrientes_2500.json")
    )

    check = await GeorefLocationChecker().check(latitude=-34.6047137, longitude=-58.4021372)

    assert check == LocationCheck(
        in_caba=True,
        province="Ciudad Autónoma de Buenos Aires",
        department="Comuna 3",
    )


@respx.mock
async def test_a_point_in_another_province_is_not_in_caba() -> None:
    respx.get(LOCATION_URL).respond(200, json=load_fixture("ubicacion_la_plata.json"))

    check = await GeorefLocationChecker().check(latitude=-34.9214, longitude=-57.9545)

    assert check == LocationCheck(in_caba=False, province="Buenos Aires", department="La Plata")


@respx.mock
async def test_a_point_outside_argentina_is_not_in_caba_and_has_no_names() -> None:
    respx.get(LOCATION_URL).respond(
        200, json=load_fixture("ubicacion_fuera_de_argentina.json")
    )

    check = await GeorefLocationChecker().check(latitude=-40.0, longitude=-30.0)

    assert check == LocationCheck(in_caba=False, province=None, department=None)


@respx.mock
async def test_forwards_the_coordinates_to_georef() -> None:
    route = respx.get(LOCATION_URL).respond(
        200, json=load_fixture("ubicacion_caba_corrientes_2500.json")
    )

    await GeorefLocationChecker().check(latitude=-34.6047137, longitude=-58.4021372)

    params = route.calls.last.request.url.params
    assert params["lat"] == "-34.6047137"
    assert params["lon"] == "-58.4021372"


@respx.mock
async def test_georef_failure_raises_location_check_error() -> None:
    respx.get(LOCATION_URL).mock(side_effect=httpx.ConnectTimeout("timeout"))

    with pytest.raises(LocationCheckError):
        await GeorefLocationChecker().check(latitude=-34.6, longitude=-58.4)


def test_source_cites_georef() -> None:
    source = GeorefLocationChecker().source

    assert "Georef" in source.name
    assert source.url == settings.georef_base_url
    assert "CC BY 4.0" in source.license
