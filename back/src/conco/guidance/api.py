from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel

from conco.guidance.domain import (
    Procedure,
    ProcedureCatalog,
    ProcedureDetail,
    ProcedureSearchError,
    Regulation,
    RegulationLookupError,
    RegulationRegistry,
    RegulationType,
    Source,
)
from conco.guidance.infrastructure import BoletinOficialRegulationRegistry, CabaProcedureCatalog

router = APIRouter(prefix="/guidance", tags=["Orientación"])

UNAVAILABLE_DETAIL = "El servicio de trámites no está disponible. Intentá de nuevo más tarde."
REGULATIONS_UNAVAILABLE_DETAIL = (
    "El Boletín Oficial no está disponible. Intentá de nuevo más tarde."
)


class ProcedureSearchResponse(BaseModel):
    """Trámites encontrados y la fuente oficial de la que provienen."""

    procedures: list[Procedure]
    source: Source


class ProcedureDetailResponse(BaseModel):
    """Detalle de un trámite y la fuente oficial de la que proviene."""

    procedure: ProcedureDetail
    source: Source


class RegulationLookupResponse(BaseModel):
    """Normas encontradas y la fuente oficial de la que provienen."""

    regulations: list[Regulation]
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


def get_regulation_registry() -> RegulationRegistry:
    """Elige qué registro de normas se usa; los tests lo reemplazan por uno falso."""
    return BoletinOficialRegulationRegistry()


@router.get(
    "/regulations/{regulation_type}/{number}/{year}",
    response_model=RegulationLookupResponse,
)
async def find_regulation(
    registry: Annotated[RegulationRegistry, Depends(get_regulation_registry)],
    regulation_type: Annotated[RegulationType, Path(description="Tipo de norma.")],
    number: Annotated[int, Path(ge=1, description="Número de la norma, por ejemplo: 6101.")],
    year: Annotated[
        int, Path(ge=1900, le=2100, description="Año de la norma con cuatro dígitos.")
    ],
) -> RegulationLookupResponse:
    """Busca una ley o un decreto de la Ciudad de Buenos Aires en el Boletín Oficial.

    La norma se muestra como referencia de la fuente oficial: CONCO no interpreta su
    alcance ni determina si se aplica a un caso concreto (RN-04). Puede haber más de una
    norma con el mismo tipo, número y año (por ejemplo, decretos del Poder Ejecutivo y de la
    Legislatura).
    """
    try:
        regulations = await registry.find(regulation_type, number, year)
    except RegulationLookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=REGULATIONS_UNAVAILABLE_DETAIL
        ) from exc
    if not regulations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró la norma solicitada en el Boletín Oficial.",
        )
    return RegulationLookupResponse(regulations=regulations, source=registry.source)
