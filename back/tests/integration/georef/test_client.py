import pytest

from conco.integrations.georef.client import locate, search_addresses

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def test_search_addresses_against_real_georef() -> None:
    result = await search_addresses("Corrientes 2500")

    assert result.count >= 1
    address = result.addresses[0]
    assert "CORRIENTES 2500" in address.nomenclature
    assert address.department.name == "Comuna 3"
    assert address.location is not None
    assert -34.7 <= address.location.lat <= -34.5
    assert -58.5 <= address.location.lon <= -58.3


async def test_locate_against_real_georef() -> None:
    caba = await locate(latitude=-34.6047137, longitude=-58.4021372)
    la_plata = await locate(latitude=-34.9214, longitude=-57.9545)

    assert caba.location.province.id == "02"
    assert caba.location.department.name == "Comuna 3"
    assert la_plata.location.province.id == "06"
