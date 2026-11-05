import pytest

from conco.integrations.georef.client import search_addresses

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
