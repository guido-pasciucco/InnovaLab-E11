from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel

from conco.guidance.domain import (
    Procedure,
    ProcedureCatalog,
    ProcedureDetail,
    ProcedureSearchError,
    Source,
)
from conco.guidance.infrastructure import CabaProcedureCatalog

router = APIRouter(prefix="/guidance", tags=["Orientación"])

UNAVAILABLE_DETAIL = "El servicio de trámites no está disponible. Intentá de nuevo más tarde."


class ProcedureSearchResponse(BaseModel):
    """Trámites encontrados y la fuente oficial de la que provienen."""

    procedures: list[Procedure]
    source: Source


class ProcedureDetailResponse(BaseModel):
    """Detalle de un trámite y la fuente oficial de la que proviene."""

    procedure: ProcedureDetail
    source: Source


def get_procedure_catalog() -> ProcedureCatalog:
    """Elige qué catálogo de trámites se usa; los tests lo reemplazan por uno falso."""
    return CabaProcedureCatalog()


@router.get("/procedures", response_model=ProcedureSearchResponse)
async def search_procedures(
    catalog: Annotated[ProcedureCatalog, Depends(get_procedure_catalog)],
    query: Annotated[
        str,
        Query(
            min_length=3,
            max_length=100,
            pattern=r"\S",
            description="Texto a buscar en el nombre del trámite, por ejemplo: habilitación.",
        ),
    ],
    limit: Annotated[
        int,
        Query(ge=1, le=20, description="Cantidad máxima de resultados."),
    ] = 10,
) -> ProcedureSearchResponse:
    """Busca trámites oficiales de la Ciudad de Buenos Aires por su nombre."""
    try:
        procedures = await catalog.search(query, limit=limit)
    except ProcedureSearchError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=UNAVAILABLE_DETAIL
        ) from exc
    return ProcedureSearchResponse(procedures=procedures, source=catalog.source)


@router.get("/procedures/{procedure_id}", response_model=ProcedureDetailResponse)
async def get_procedure(
    catalog: Annotated[ProcedureCatalog, Depends(get_procedure_catalog)],
    procedure_id: Annotated[UUID, Path(description="Id del trámite devuelto por la búsqueda.")],
) -> ProcedureDetailResponse:
    """Devuelve requisitos, pasos, organismo responsable y enlace oficial de un trámite."""
    try:
        procedure = await catalog.get(procedure_id)
    except ProcedureSearchError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=UNAVAILABLE_DETAIL
        ) from exc
    if procedure is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró el trámite solicitado.",
        )
    return ProcedureDetailResponse(procedure=procedure, source=catalog.source)
