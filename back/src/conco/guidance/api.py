from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel

from conco.guidance.activity_directory import PostgresActivityDirectory
from conco.guidance.domain import (
    Activity,
    ActivityDirectory,
    ActivityDirectoryError,
    ActivitySuggestion,
    ApplicableProcedure,
    Procedure,
    ProcedureCatalog,
    ProcedureDetail,
    ProcedureSearchError,
    Source,
)
from conco.guidance.embeddings import FastEmbedTextEmbedder
from conco.guidance.infrastructure import CabaProcedureCatalog

router = APIRouter(prefix="/guidance", tags=["Orientación"])

UNAVAILABLE_DETAIL = "El servicio de trámites no está disponible. Intentá de nuevo más tarde."
ACTIVITIES_UNAVAILABLE_DETAIL = (
    "La búsqueda de actividades no está disponible. Intentá de nuevo más tarde."
)


class ProcedureSearchResponse(BaseModel):
    """Trámites encontrados y la fuente oficial de la que provienen."""

    procedures: list[Procedure]
    source: Source


class ProcedureDetailResponse(BaseModel):
    """Detalle de un trámite y la fuente oficial de la que proviene."""

    procedure: ProcedureDetail
    source: Source


class ActivitySuggestionsResponse(BaseModel):
    """Actividades curadas parecidas al texto, de la más a la menos parecida."""

    activities: list[ActivitySuggestion]


class ActivityProceduresResponse(BaseModel):
    """Trámites que suelen aplicar a una actividad y la fuente oficial de la que provienen."""

    activity: Activity
    procedures: list[ApplicableProcedure]
    source: Source


def get_procedure_catalog() -> ProcedureCatalog:
    """Elige qué catálogo de trámites se usa; los tests lo reemplazan por uno falso."""
    return CabaProcedureCatalog()


def get_activity_directory() -> ActivityDirectory:
    """Elige qué directorio de actividades se usa; los tests lo reemplazan por uno falso."""
    return PostgresActivityDirectory(FastEmbedTextEmbedder())


@router.get("/activities", response_model=ActivitySuggestionsResponse)
async def suggest_activities(
    directory: Annotated[ActivityDirectory, Depends(get_activity_directory)],
    query: Annotated[
        str,
        Query(
            min_length=2,
            max_length=100,
            pattern=r"\S",
            description="Lo que la persona quiere hacer, por ejemplo: quiero poner una barbería.",
        ),
    ],
    limit: Annotated[
        int,
        Query(ge=1, le=10, description="Cantidad máxima de actividades sugeridas."),
    ] = 5,
) -> ActivitySuggestionsResponse:
    """Sugiere actividades comerciales parecidas por significado al texto escrito."""
    try:
        activities = await directory.suggest(query, limit=limit)
    except ActivityDirectoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ACTIVITIES_UNAVAILABLE_DETAIL,
        ) from exc
    return ActivitySuggestionsResponse(activities=activities)


@router.get("/activities/{slug}/procedures", response_model=ActivityProceduresResponse)
async def get_activity_procedures(
    directory: Annotated[ActivityDirectory, Depends(get_activity_directory)],
    catalog: Annotated[ProcedureCatalog, Depends(get_procedure_catalog)],
    slug: Annotated[
        str,
        Path(
            max_length=60,
            pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$",
            description="Identificador de la actividad devuelto por la sugerencia.",
        ),
    ],
) -> ActivityProceduresResponse:
    """Devuelve los trámites que suelen aplicar a la actividad, con cuándo aplica cada uno."""
    try:
        result = await directory.procedures_for(slug)
    except ActivityDirectoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ACTIVITIES_UNAVAILABLE_DETAIL,
        ) from exc
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró la actividad solicitada.",
        )
    return ActivityProceduresResponse(
        activity=result.activity, procedures=result.procedures, source=catalog.source
    )


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
