import asyncio
from datetime import datetime, timezone
from uuid import UUID

import pytest

from conco.integrations.caba_tramites.models import (
    CabaPath,
    CabaProcedure,
    CabaProcedureAttributes,
    CabaProcedureDetail,
    CabaRequirementItem,
    CabaText,
)
from conco.guidance.load_requirements import (
    RequirementSyncError,
    detail_to_rows,
    fetch_requirement_rows,
)

HABILITACION_ID = UUID("338718b4-a2a0-44af-baa4-083f5d834b12")
EXPRES_ID = UUID("15e0394b-c7b5-4f93-bc25-ee012d695aec")
CHANGED = datetime(2026, 8, 7, tzinfo=timezone.utc)


def _detail(procedure_id: UUID, items: list[tuple[str | None, list[str]]]) -> CabaProcedureDetail:
    return CabaProcedureDetail(
        procedure=CabaProcedure(
            id=procedure_id,
            attributes=CabaProcedureAttributes(
                title="Trámite de prueba",
                path=CabaPath(alias="/tramites/prueba"),
                changed=CHANGED,
                body=CabaText(value="Resumen", format="plain_text"),
            ),
        ),
        requirements=[
            CabaRequirementItem(
                heading=heading,
                bodies=[CabaText(value=body, format="full_html") for body in bodies],
            )
            for heading, bodies in items
        ],
        steps=[],
        responsible_office=None,
        start_button=None,
    )


def test_rows_keep_heading_separate_from_body_text() -> None:
    detail = _detail(
        HABILITACION_ID,
        [("Requisitos obligatorios", ["<p>Sin inflamables.</p>", "<p>Encomienda firmada.</p>"]),
         (None, ["<p>Contar con miBA nivel 3.</p>"])],
    )

    rows = detail_to_rows(HABILITACION_ID, detail)

    assert rows == [
        (HABILITACION_ID, 0, "Requisitos obligatorios", "Sin inflamables."),
        (HABILITACION_ID, 1, "Requisitos obligatorios", "Encomienda firmada."),
        (HABILITACION_ID, 2, None, "Contar con miBA nivel 3."),
    ]


def test_fetch_uses_the_given_fetcher_and_ignores_duplicates() -> None:
    requests: list[UUID] = []

    async def fetcher(procedure_id: UUID):
        requests.append(procedure_id)
        return _detail(procedure_id, [(None, ["<p>Req A</p>"])])

    rows = asyncio.run(fetch_requirement_rows(fetcher, [HABILITACION_ID, HABILITACION_ID]))

    assert requests == [HABILITACION_ID]
    assert rows == [(HABILITACION_ID, 0, None, "Req A")]


def test_missing_detail_fails_loudly_listing_the_missing_ids() -> None:
    async def fetcher(procedure_id: UUID):
        return _detail(procedure_id, [(None, ["<p>Req A</p>"])]) if procedure_id == HABILITACION_ID else None

    with pytest.raises(RequirementSyncError) as excinfo:
        asyncio.run(fetch_requirement_rows(fetcher, [HABILITACION_ID, EXPRES_ID]))

    assert str(EXPRES_ID) in str(excinfo.value)
