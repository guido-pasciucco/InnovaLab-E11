import json
from pathlib import Path
from typing import Any

import pytest
import respx

from conco.config import settings
from conco.geolocation.domain import Address, AddressSearchError, Coordinates
from conco.geolocation.infrastructure import GeorefAddressFinder

pytestmark = pytest.mark.anyio

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures" / "georef"
ADDRESSES_URL = f"{settings.georef_base_url}/direcciones"


def load_fixture(name: str) -> Any:
    """Lee una respuesta real de Georef guardada en tests/fixtures/georef/."""
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


@respx.mock
async def test_maps_a_full_georef_result_to_domain_addresses() -> None:
    respx.get(ADDRESSES_URL).respond(
        200, json=load_fixture("direcciones_corrientes_2500.json")
    )

    addresses = await GeorefAddressFinder().search(
        "Corrientes 2500", province="caba", limit=5
    )

    assert addresses == [
        Address(
            full_address="AV CORRIENTES 2500, Comuna 3, Ciudad Autónoma de Buenos Aires",
            street="AV CORRIENTES",
            number=2500,
            department="Comuna 3",
            locality="Ciudad Autónoma de Buenos Aires",
            province="Ciudad Autónoma de Buenos Aires",
            coordinates=Coordinates(
                latitude=-34.6047137500375, longitude=-58.402137170712
            ),
        )
    ]


@respx.mock
async def test_forwards_province_and_limit_to_georef() -> None:
    route = respx.get(ADDRESSES_URL).respond(
        200, json=load_fixture("direcciones_sin_resultados.json")
    )

    await GeorefAddressFinder().search("San Martín 100", province="cordoba", limit=3)

    params = route.calls.last.request.url.params
    assert params["provincia"] == "cordoba"
    assert params["max"] == "3"


@respx.mock
async def test_street_without_number_maps_to_none_number() -> None:
    respx.get(ADDRESSES_URL).respond(
        200, json=load_fixture("direcciones_sin_altura.json")
    )

    addresses = await GeorefAddressFinder().search("Corrientes", province="caba", limit=5)

    assert addresses[0].number is None
    assert addresses[0].coordinates is not None


@respx.mock
async def test_address_without_location_maps_to_none_coordinates() -> None:
    payload = load_fixture("direcciones_corrientes_2500.json")
    payload["direcciones"][0].pop("ubicacion")
    respx.get(ADDRESSES_URL).respond(200, json=payload)

    addresses = await GeorefAddressFinder().search(
        "Corrientes 2500", province="caba", limit=5
    )

    assert addresses[0].coordinates is None


@respx.mock
async def test_no_results_returns_empty_list() -> None:
    respx.get(ADDRESSES_URL).respond(
        200, json=load_fixture("direcciones_sin_resultados.json")
    )

    addresses = await GeorefAddressFinder().search(
        "Calle Inventada Xyz 9999", province="caba", limit=5
    )

    assert addresses == []


@respx.mock
async def test_georef_failure_raises_address_search_error() -> None:
    respx.get(ADDRESSES_URL).respond(500, text="Internal Server Error")

    with pytest.raises(AddressSearchError):
        await GeorefAddressFinder().search("Corrientes 2500", province="caba", limit=5)
