from uuid import UUID

import pytest

from conco.integrations.caba_tramites.client import get_procedure, search_procedures

pytestmark = [pytest.mark.anyio, pytest.mark.integration]

HABILITACION_ID = UUID("338718b4-a2a0-44af-baa4-083f5d834b12")


async def test_search_and_get_procedure_against_real_api() -> None:
    result = await search_procedures("habilitación de actividad económica")

    assert HABILITACION_ID in [procedure.id for procedure in result.procedures]

    detail = await get_procedure(HABILITACION_ID)

    assert detail is not None
    assert detail.procedure.attributes.path.alias.startswith("/tramites/")
    assert detail.requirements
    assert detail.steps
    assert detail.responsible_office is not None


async def test_unknown_procedure_against_real_api_returns_none() -> None:
    assert await get_procedure(UUID("00000000-0000-0000-0000-000000000000")) is None
