import json
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from conco.config import settings
from conco.integrations.georef.client import GeorefError, locate

pytestmark = pytest.mark.anyio

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures" / "georef"
LOCATION_URL = f"{settings.georef_base_url}/ubicacion"


def load_fixture(name: str) -> Any:
    """Lee una respuesta real de Georef guardada en tests/fixtures/georef/."""
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


@respx.mock
async def test_locate_parses_a_point_in_caba() -> None:
    respx.get(LOCATION_URL).respond(
        200, json=load_fixture("ubicacion_caba_corrientes_2500.json")
    )

    result = await locate(latitude=-34.6047137, longitude=-58.4021372)

    location = result.location
    assert location.province.id == "02"
    assert location.province.name == "Ciudad Autónoma de Buenos Aires"
    assert location.department.name == "Comuna 3"
    assert location.municipality.name == "Comuna 3"
    assert location.lat == pytest.approx(-34.6047137)
    assert location.lon == pytest.approx(-58.4021372)


@respx.mock
async def test_locate_sends_lat_and_lon() -> None:
    route = respx.get(LOCATION_URL).respond(
        200, json=load_fixture("ubicacion_caba_corrientes_2500.json")
    )

    await locate(latitude=-34.6047137, longitude=-58.4021372)

    params = route.calls.last.request.url.params
    assert params["lat"] == "-34.6047137"
    assert params["lon"] == "-58.4021372"


@respx.mock
async def test_locate_parses_a_point_in_another_province() -> None:
    respx.get(LOCATION_URL).respond(200, json=load_fixture("ubicacion_la_plata.json"))

    result = await locate(latitude=-34.9214, longitude=-57.9545)

    assert result.location.province.id == "06"
    assert result.location.province.name == "Buenos Aires"
    assert result.location.department.name == "La Plata"


@respx.mock
async def test_locate_outside_argentina_has_null_entities() -> None:
    respx.get(LOCATION_URL).respond(
        200, json=load_fixture("ubicacion_fuera_de_argentina.json")
    )

    result = await locate(latitude=-40.0, longitude=-30.0)

    location = result.location
    assert location.province.id is None
    assert location.province.name is None
    assert location.department.name is None
    assert location.municipality.name is None


@respx.mock
async def test_locate_http_error_raises_georef_error() -> None:
    respx.get(LOCATION_URL).respond(400, json=load_fixture("error_400_lat_invalida.json"))

    with pytest.raises(GeorefError):
        await locate(latitude=-34.6, longitude=-58.4)


@respx.mock
async def test_locate_timeout_raises_georef_error() -> None:
    respx.get(LOCATION_URL).mock(side_effect=httpx.ConnectTimeout("timeout"))

    with pytest.raises(GeorefError):
        await locate(latitude=-34.6, longitude=-58.4)


@respx.mock
async def test_locate_unexpected_payload_raises_georef_error() -> None:
    respx.get(LOCATION_URL).respond(200, json={"foo": 1})

    with pytest.raises(GeorefError):
        await locate(latitude=-34.6, longitude=-58.4)


@respx.mock
async def test_locate_non_json_body_raises_georef_error() -> None:
    respx.get(LOCATION_URL).respond(200, text="<html>Mantenimiento</html>")

    with pytest.raises(GeorefError):
        await locate(latitude=-34.6, longitude=-58.4)
