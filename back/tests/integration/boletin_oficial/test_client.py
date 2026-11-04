import pytest

from conco.integrations.boletin_oficial.client import BoletinOficialNormType, find_norms

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def test_find_law_and_decree_against_real_boletin_oficial() -> None:
    laws = await find_norms(BoletinOficialNormType.LEY, 6101, 2018)

    assert [norm.id for norm in laws] == [435567]
    assert laws[0].documents[0].url is not None
    assert laws[0].documents[0].url.startswith("https://")

    decrees = await find_norms(BoletinOficialNormType.DECRETO, 40, 2019)

    assert [norm.id for norm in decrees] == [438789]


async def test_unknown_norm_against_real_boletin_oficial_returns_empty_list() -> None:
    assert await find_norms(BoletinOficialNormType.LEY, 6101, 2019) == []
