"""Trae los requisitos de los trámites ya cargados en la base y los persiste relacionados.

Uso (desde back/, con la base levantada):

    uv run python -m conco.guidance.load_requirements

No re-corre el catálogo completo: lee los `id` presentes en `public.procedures`,
pide el detalle oficial de cada uno y reescribe `public.procedure_requirements` en
una sola transacción. Si algún trámite ya no existe, no se toca la base.

Los encabezados (`field_texto`) se guardan como su propia columna `heading`, separados
del cuerpo; los cuerpos quedan como texto plano de una sola línea.
"""

import asyncio
from collections.abc import Awaitable, Callable
from uuid import UUID

import psycopg

from conco.config import settings
from conco.guidance.infrastructure import html_to_text
from conco.integrations.caba_tramites.client import get_procedure
from conco.integrations.caba_tramites.models import CabaProcedureDetail, CabaText


class RequirementSyncError(Exception):
    """No se pudieron traer los requisitos de los trámites indicados."""


def _plain(text: CabaText) -> str:
    if text.format == "plain_text":
        return " ".join(text.value.split())
    return html_to_text(text.value)


def detail_to_rows(
    procedure_id: UUID, detail: CabaProcedureDetail
) -> list[tuple[UUID, int, str | None, str]]:
    """Aplana un detalle a filas `(procedure_id, position, heading, text)`.

    Una fila por cuerpo no vacío, en el orden de la página; el encabezado del ítem,
    si tiene, se repite en cada fila del ítem y queda como columna propia.
    """
    rows: list[tuple[UUID, int, str | None, str]] = []
    position = 0
    for item in detail.requirements:
        heading = html_to_text(item.heading) if item.heading else None
        if not heading:
            heading = None
        for body in item.bodies:
            text = _plain(body)
            if text:
                rows.append((procedure_id, position, heading, text))
                position += 1
    return rows


async def fetch_requirement_rows(
    fetch_detail: Callable[[UUID], Awaitable[CabaProcedureDetail | None]],
    procedure_ids: list[UUID] | tuple[UUID, ...],
) -> list[tuple[UUID, int, str | None, str]]:
    """Devuelve las filas de requisitos, o falla listando los trámites que faltan."""
    ids = list(dict.fromkeys(procedure_ids))
    details = await asyncio.gather(*(fetch_detail(procedure_id) for procedure_id in ids))
    missing = [str(procedure_id) for procedure_id, detail in zip(ids, details) if detail is None]
    if missing:
        raise RequirementSyncError(
            "La Ciudad ya no publica los trámites presentes en la base: " + ", ".join(sorted(missing))
        )
    return [
        row for procedure_id, detail in zip(ids, details) for row in detail_to_rows(procedure_id, detail)
    ]


def replace_requirement_rows(
    cursor, rows: list[tuple[UUID, int, str | None, str]]  # noqa: ANN001 - cursor de psycopg
) -> None:
    """Reescribe la tabla completa dentro de la transacción del llamador."""
    cursor.execute("truncate public.procedure_requirements")
    if rows:
        cursor.executemany(
            "insert into public.procedure_requirements (procedure_id, position, heading, text) "
            "values (%s, %s, %s, %s)",
            rows,
        )


def load(database_url: str) -> None:
    with psycopg.connect(database_url) as conn, conn.cursor() as cursor:
        cursor.execute("select id from public.procedures order by id")
        procedure_ids = [row[0] for row in cursor.fetchall()]
    if not procedure_ids:
        raise SystemExit("No hay trámites en la base; corré primero `uv run python -m conco.guidance.load_catalog`.")

    rows = asyncio.run(fetch_requirement_rows(get_procedure, procedure_ids))
    if not rows:
        raise SystemExit("Los trámites cargados no publican requisitos; no se modificó la base.")

    with psycopg.connect(database_url) as conn, conn.cursor() as cursor:
        replace_requirement_rows(cursor, rows)
    print(f"Requerimientos cargados: {len(rows)} ítems para {len(procedure_ids)} trámites.")


if __name__ == "__main__":
    load(settings.database_url)
