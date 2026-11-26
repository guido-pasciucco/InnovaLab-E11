"""Endpoints públicos del cuadro de usos de Ciudad 3D."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from conco.errors import TerritoryUnavailable
from conco.territory.domain import (
    ParcelGeometry,
    ParcelGeometryResolver,
    RubroReferences,
    RubroReferencesResolver,
    TerritoryLookupError,
    UseTable,
    UseTableResolver,
)
from conco.territory.infrastructure import (
    UsigParcelGeometryResolver,
    UsigRubroReferencesResolver,
    UsigUseTableResolver,
)

router = APIRouter(prefix="/territory", tags=["Territorio"])


def get_use_table_resolver() -> UseTableResolver:
    """Elige qué servicio resuelve el cuadro; los tests lo reemplazan por uno falso."""
    return UsigUseTableResolver()


def get_references_resolver() -> RubroReferencesResolver:
    """Elige qué servicio devuelve las condiciones; los tests lo reemplazan."""
    return UsigRubroReferencesResolver()


def get_parcel_geometry_resolver() -> ParcelGeometryResolver:
    """Elige qué servicio devuelve la geometría; expone `resolve()` para la DI."""
    return UsigParcelGeometryResolver()


@router.get("/use-table", response_model=UseTable)
async def use_table(
    resolver: Annotated[UseTableResolver, Depends(get_use_table_resolver)],
    lat: Annotated[
        float,
        Query(ge=-90, le=90, description="Latitud del punto a consultar en el mapa."),
    ],
    lng: Annotated[
        float,
        Query(ge=-180, le=180, description="Longitud del punto a consultar en el mapa."),
    ],
) -> UseTable:
    """Devuelve el cuadro de usos completo de la parcela que contiene el punto."""
    try:
        return await resolver.resolve(lat, lng)
    except TerritoryLookupError as exc:
        raise TerritoryUnavailable() from exc


@router.get("/rubro-referencias", response_model=RubroReferences)
async def rubro_referencias(
    resolver: Annotated[RubroReferencesResolver, Depends(get_references_resolver)],
    smp: Annotated[
        str,
        Query(min_length=1, max_length=32, pattern=r"\S", description="SMP de la parcela."),
    ],
    categoria: Annotated[
        int,
        Query(ge=1, le=10, description="Identificador de la categoría del cuadro."),
    ],
    mixtura: Annotated[
        int,
        Query(ge=0, le=10, description="Área de mixtura de usos de la parcela."),
    ],
    rubro: Annotated[
        int,
        Query(ge=1, le=1000, description="Identificador del rubro consultado."),
    ],
) -> RubroReferences:
    """Devuelve las condiciones del rubro seleccionado como texto de referencia."""
    try:
        return await resolver.resolve(smp, categoria, mixtura, rubro)
    except TerritoryLookupError as exc:
        raise TerritoryUnavailable() from exc


@router.get("/parcel-geometry", response_model=ParcelGeometry)
async def parcel_geometry(
    resolver: Annotated[ParcelGeometryResolver, Depends(get_parcel_geometry_resolver)],
    smp: Annotated[
        str,
        Query(min_length=1, max_length=32, pattern=r"\S", description="SMP de la parcela."),
    ],
) -> ParcelGeometry:
    """Devuelve la geometría GeoJSON de la parcela para dibujarla en el mapa."""
    try:
        return await resolver.resolve(smp)
    except TerritoryLookupError as exc:
        raise TerritoryUnavailable() from exc
