import pytest

from conco.integrations.usig.client import (
    get_datos_utiles_by_address,
    get_datos_utiles_by_coordinates,
)

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def test_datos_utiles_by_address_and_coordinates_against_real_usig() -> None:
    by_address = await get_datos_utiles_by_address("Corrientes", 2500)

    assert by_address is not None
    assert by_address.commune == "Comuna 3"
    assert by_address.neighborhood == "Balvanera"
    assert by_address.postal_code
    assert by_address.argentine_postal_code

    by_coordinates = await get_datos_utiles_by_coordinates(
        longitude=-58.401981, latitude=-34.604792
    )

    assert by_coordinates is not None
    assert by_coordinates.commune == "Comuna 3"


async def test_unknown_street_and_point_outside_caba_against_real_usig() -> None:
    assert await get_datos_utiles_by_address("Calle Inexistente Xyz", 1234) is None
    assert (
        await get_datos_utiles_by_coordinates(longitude=-58.7567541, latitude=-34.6423652)
        is None
    )
